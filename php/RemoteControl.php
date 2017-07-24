<?php

# This file is a part of Panasonic Viera Remote control tool
#
# Copyright (c) 2017 Pierre GINDRAUD
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

require_once __DIR__ . '/constants.inc.php';
require_once __DIR__ . '/exceptions.inc.php';


/**
 * Description of RemoteControl
 *
 * @author pgindraud
 */
class RemoteControl {

    protected $host;

    protected $port;

    protected $timeout;

    public function __construct($host = null, $port = DEFAULT_PORT, $timeout = DEFAULT_TIMEOUT) {
        $this->port = $port;
        $this->host = $host;
        $this->timeout = $timeout;
    }

    /**
     * Find a TV on the network
     *
     * @return [list] the list of discovered TVs
     *    This list contains a dict per TV
     *    Each dict contains at least the 'address' key which contains the TV's IP address
     */
    public function find() {
        $tvs = [];

        $udpsock = socket_create(AF_INET, SOCK_DGRAM, SOL_UDP);
        socket_set_timeout($udpsock, DEFAULT_FIND_TIMEOUT);
        socket_set_option($udpsock, SOL_SOCKET, SO_REUSEADDR, true);
        socket_bind($udpsock, "", DEFAULT_FIND_LOCAL_PORT);
        socket_set_option($udpsock, SOL_SOCKET, MCAST_JOIN_GROUP, DEFAULT_FIND_MULTICAST_ADDRESS + "");
        socket_set_option($udpsock, SOL_SOCKET, IP_MULTICAST_TTL, 2);
        socket_set_option($udpsock, SOL_SOCKET, IP_MULTICAST_LOOP, 1);

        $find_body = sprintf(
            'M-SEARCH * HTTP/1.1\r\n' .
            'HOST:%s:{port}\r\n' .
            'MAN:"ssdp:discover"\r\n' .
            'ST:urn:panasonic-com:device:p00RemoteController:1\r\n' .
            'MX:1\r\n\r\n',
            DEFAULT_FIND_MULTICAST_ADDRESS,
            DEFAULT_FIND_MULTICAST_PORT);


        //        try:
//            g_logger.debug("Sending multicast discovery request")
//            udpsock.sendto(find_body, (DEFAULT_FIND_MULTICAST_ADDRESS, DEFAULT_FIND_MULTICAST_PORT))
//            g_logger.debug("Listen for incoming discovery replies")
//            while True:
//                data, addr = udpsock.recvfrom(2048)
//                request, head = data.decode().split('\r\n', 1)
//                g_logger.debug("Received response from %s : '''%s'''", addr, head)
//
//                headers = HeadersParser().parsestr(head, True)
//                tv = dict()
//                tv['address'] = addr[0]
//                tv['discovery'] = dict(headers.items())
//                tvs.append(tv)
//                g_logger.info("Found TV %s", tv['address'])
//        except (socket.timeout) as e:
//            g_logger.debug(str(e))
//            g_logger.info("No more TV's found")
//        except (socket.error, URLError) as e:
//            g_logger.fatal(str(e))
        socket_close($udpsock);
        return $tvs;
    }

    /**
     * Send a SOAP request to the TV.
     *
     * @param [str] url  the query part of the url
     * @param [str] urn  the resource identifier
     * @param [str] params other query params
     * @return [str] the response body
     */
    public function soapRequest($url, $urn, $action, $params) {
        $soap_body = sprintf(
            '<?xml version="1.0" encoding="utf-8"?>' .
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"' .
            ' s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">' .
            '<s:Body>' .
            '<m:%s xmlns:m="urn:%s">' .
            '%s' .
            '</m:%s>' .
            '</s:Body>' .
            '</s:Envelope>',
            $action, $urn, $params, $action);

        $headers = [
            sprintf('Host: %s:%s', $this->host, $this->port),
            sprintf('Content-Length: %d', strlen($soap_body)),
            'Content-Type: text/xml; charset="utf-8"',
            sprintf('SOAPAction: "urn:%s#%s"', $urn, $action)
        ];

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, sprintf('http://%s:%d/%s', $this->host, $this->port, $url));
        curl_setopt($ch, CURLOPT_TIMEOUT, DEFAULT_TIMEOUT);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $soap_body);

        $res = curl_exec ($ch);
        if ($res === FALSE) {
            throw new RemoteControlException("The TV is unreacheable.");
        }
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE );
        if ($http_code != 200) {
            throw new UserControlException("This command has failed, maybe the TV does not support it.");
        }

        curl_close($ch);
        return $res;
    }

    /**
     * Send a key command to the TV.
     *
     * @param [str] key a predefined keys from Keys enum
     */
    public function sendKey($key) {
        if ($this->host === null) {
            throw new UserControlException("You must set the host value to used this feature.");
        }
        $params = sprintf('<X_KeyEvent>%s</X_KeyEvent>', $key);
        $this->soapRequest(URL_CONTROL_NRC, URN_REMOTE_CONTROL,
                          'X_SendKey', $params);
    }

    /**
     * Return the current volume level.
     *
     * @return [int] the volume value
     */
    public function getVolume() {
        $params = '<InstanceID>0</InstanceID><Channel>Master</Channel>';
        $res = $this->soapRequest(URL_CONTROL_DMR,
                                    URN_RENDERING_CONTROL,
                                    'GetVolume',
                                    $params);
        $elm = simplexml_load_string($res);
        if ($elm === FALSE) {
            throw new RemoteControlException("The TV has returned a bad XML value");
        }
        $vol = $elm->xpath('.//CurrentVolume');
        if (! isset($vol[0])) {
            throw new RemoteControlException("The TV has returned a bad volume value");
        }
        return intval($vol[0]);
    }

    /**
     * Set a new volume level
     *
     * @param [int] the new value for volume
     */
    public function setVolume($volume) {
        if ($volume < 0 || $volume > 100) {
            throw new UserControlException("Bad value for volume control. It must be between 0 and 100.");
        }
        $params = sprintf('<InstanceID>0</InstanceID><Channel>Master</Channel>' .
                           '<DesiredVolume>%s</DesiredVolume>', $volume);
        $this->soapRequest(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                          'SetVolume', $params);
    }

    /**
     * Return if the TV is muted
     *
     * @return [bool] the mute status
     */
    public function getMute() {
        $params = '<InstanceID>0</InstanceID><Channel>Master</Channel>';
        $res = $this->soapRequest(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                                'GetMute', $params);
        $elm = simplexml_load_string($res);
        if ($elm === FALSE) {
            throw new RemoteControlException("The TV has returned a bad XML value");
        }
        $mute = $elm->xpath('.//CurrentMute');
        if (! isset($mute[0])) {
            throw new RemoteControlException("The TV has returned a bad mute status");
        }
        return $mute[0] != '0';
    }

    /**
     * Mute or unmute the TV.
     *
     * @param [bool] true if mute must be enabled, false if not
     */
    public function setMute($enable) {
        if (boolval($enable)) {
            $data = '1';
        } else {
            $data = '0';
        }
        $params = sprintf('<InstanceID>0</InstanceID><Channel>Master</Channel>' .
                  '<DesiredMute>%s</DesiredMute>', $data);
        $this->soapRequest(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                          'SetMute', $params);
    }
}
