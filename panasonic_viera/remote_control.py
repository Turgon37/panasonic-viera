# -*- coding: utf8 -*-

# Systems imports
from email.parser import Parser as HeadersParser
import socket
import sys
import xml.etree.ElementTree as xml_elm
if sys.version_info[0] == 3:
    from urllib.request import urlopen, Request, URLError, HTTPError
    from socketserver import UDPServer, BaseRequestHandler
    from io import StringIO
else:
    from urllib2 import urlopen, Request, URLError, HTTPError
    from SocketServer import UDPServer, BaseRequestHandler
    from StringIO import StringIO

# Project imports
from .constants import Keys
from .utils import getLogger
from .exceptions import RemoteControlException, UserControlException

# Global vars
g_logger = getLogger()

URN_RENDERING_CONTROL = 'schemas-upnp-org:service:RenderingControl:1'
URN_REMOTE_CONTROL = 'panasonic-com:service:p00NetworkControl:1'

URL_CONTROL_DMR = 'dmr/control_0'
URL_CONTROL_NRC = 'nrc/control_0'

DEFAULT_PORT = 55000
DEFAULT_TIMEOUT = 2
DEFAULT_FIND_TIMEOUT = 3

DEFAULT_FIND_LOCAL_PORT = 60000
DEFAULT_FIND_MULTICAST_ADDRESS = "239.255.255.250"
DEFAULT_FIND_MULTICAST_PORT = 1900


class RemoteControl:
    """This is a remote control client
    """

    def __init__(self, host=None, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT):
        """Default constructor
        """
        self.__host = host
        self.__port = port
        self.__timeout = timeout

    def find(self, multicast_address=DEFAULT_FIND_MULTICAST_ADDRESS, multicast_port=DEFAULT_FIND_MULTICAST_PORT, multicast_localport=DEFAULT_FIND_LOCAL_PORT):
        """Find a TV on the network

        @return [list] the list of discovered TVs
            This list contains a dict per TV
            Each dict contains at least the 'address' key which contains the TV's IP address
        """
        tvs = []
        udpsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udpsock.settimeout(DEFAULT_FIND_TIMEOUT)
        udpsock.setsockopt(socket.IPPROTO_IP, socket.SO_REUSEADDR, True)
        udpsock.bind((str(socket.INADDR_ANY), multicast_localport))
        udpsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(multicast_address) + socket.inet_aton(str(socket.INADDR_ANY)))
        udpsock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        udpsock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        g_logger.debug("UDP Multicast socket ready on request on %s : %d", socket.INADDR_ANY, multicast_localport)

        find_body = (
            'M-SEARCH * HTTP/1.1\r\n'
            'HOST:{address}:{port}\r\n'
            'MAN:"ssdp:discover"\r\n'
            'ST:urn:panasonic-com:device:p00RemoteController:1\r\n'
            'MX:1\r\n\r\n'
        ).format(address=multicast_address, port=multicast_port).encode('utf-8')

        try:
            g_logger.debug("Sending multicast discovery request")
            udpsock.sendto(find_body, (multicast_address, multicast_port))
            g_logger.debug("Listen for incoming discovery replies")
            while True:
                data, addr = udpsock.recvfrom(2048)
                request, head = data.decode().split('\r\n', 1)
                g_logger.debug("Received response from %s : '''%s'''", addr, head)

                headers = HeadersParser().parsestr(head, True)
                tv = dict()
                tv['address'] = addr[0]
                tv['discovery'] = dict(headers.items())
                tvs.append(tv)
                g_logger.info("Found TV %s", tv['address'])
        except (socket.timeout) as e:
            g_logger.debug(str(e))
            g_logger.info("No more TV's found")
        except (socket.error, URLError) as e:
            g_logger.fatal(str(e))
        udpsock.close()
        return tvs

    def soapRequest(self, url, urn, action, params):
        """Send a SOAP request to the TV.

        @param [str] url  the query part of the url
        @param [str] urn  the resource identifier
        @param [str] params other query params

        @return [str] the response body
        """
        soap_body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"'
            ' s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            '<s:Body>'
            '<m:{action} xmlns:m="urn:{urn}">'
            '{params}'
            '</m:{action}>'
            '</s:Body>'
            '</s:Envelope>'
        ).format(action=action, urn=urn, params=params).encode('utf-8')

        headers = {
            'Host': '{}:{}'.format(self.__host, self.__port),
            'Content-Length': len(soap_body),
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPAction': '"urn:{}#{}"'.format(urn, action),
        }

        url = 'http://{}:{}/{}'.format(self.__host, self.__port, url)

        g_logger.debug("Sending request to %s: with headers : %s and body : '''%s'''", url, headers, soap_body)
        req = Request(url, soap_body, headers)

        try:
            res = urlopen(req, timeout=self.__timeout).read()
        except HTTPError as e:
            g_logger.fatal(str(e))
            raise UserControlException("This command has failed, maybe the TV does not support it.")
        except (socket.error, socket.timeout, URLError) as e:
            g_logger.fatal(str(e))
            raise RemoteControlException("The TV is unreacheable.")
        if sys.version_info[0] == 3:
            g_logger.debug("Received response: '''%s'''", res.decode())
        else:
            g_logger.debug("Received response: '''%s'''", res)
        return res

    def sendKey(self, key):
        """Send a key command to the TV.

        @param [str] key a predefined keys from Keys enum
        """
        if self.__host is None:
            raise UserControlException("You must set the host value to used this feature.")
        if isinstance(key, Keys):
            key = key.value
        params = '<X_KeyEvent>{}</X_KeyEvent>'.format(key)
        g_logger.info("Send Key %s to %s", key, self.__host)
        self.soapRequest(URL_CONTROL_NRC, URN_REMOTE_CONTROL,
                          'X_SendKey', params)

    def getVolume(self):
        """Return the current volume level.

        @return [int] the volume value
        """
        params = '<InstanceID>0</InstanceID><Channel>Master</Channel>'
        g_logger.info("Send GetVolume request to %s", self.__host)
        res = self.soapRequest(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                                'GetVolume', params)
        root = xml_elm.fromstring(res)
        el_volume = root.find('.//CurrentVolume')
        return int(el_volume.text)

    def setVolume(self, volume):
        """Set a new volume level

        @param [int] the new value for volume
        """
        if volume > 100 or volume < 0:
            raise UserControlException("Bad value for volume control. It must be between 0 and 100.")
        params = ('<InstanceID>0</InstanceID><Channel>Master</Channel>'
                  '<DesiredVolume>{}</DesiredVolume>').format(volume)
        g_logger.info("Send SetVolume request to %s", self.__host)
        self.soapRequest(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                          'SetVolume', params)

    def getMute(self):
        """Return if the TV is muted

        @return [bool] the mute status
        """
        params = '<InstanceID>0</InstanceID><Channel>Master</Channel>'
        g_logger.info("Send GetMute request to %s", self.__host)
        res = self.soapRequest(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                                'GetMute', params)
        root = xml_elm.fromstring(res)
        el_mute = root.find('.//CurrentMute')
        return el_mute.text != '0'

    def setMute(self, enable):
        """Mute or unmute the TV.

        @param [bool] true if mute must be enabled, false if not
        """
        data = '1' if enable else '0'
        params = ('<InstanceID>0</InstanceID><Channel>Master</Channel>'
                  '<DesiredMute>{}</DesiredMute>').format(data)
        g_logger.info("Send SetMute request to %s", self.__host)
        self.soapRequest(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                          'SetMute', params)
