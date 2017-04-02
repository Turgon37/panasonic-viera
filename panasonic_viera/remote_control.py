# -*- coding: utf8 -*-

# Systems imports
import socket
import sys
import xml.etree.ElementTree as xml_elm
if sys.version_info[0] == 3:
    from urllib.request import urlopen, Request, URLError, HTTPError
else:
    from urllib2 import urlopen, Request, URLError, HTTPError

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

class RemoteControl:
    """This is a remote control client
    """

    def __init__(self, host, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT):
        """Default constructor
        """
        self.__host = host
        self.__port = port
        self.__timeout = timeout

    def soap_request(self, url, urn, action, params):
        """Send a SOAP request to the TV.

        @param [str] url  the query part of the url
        @param [str] urn  the resource identifier
        @param [str] params other query params
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
            'Content-Type': 'text/xml; charset=utf-8"',
            'SOAPAction': '"urn:{}#{}"'.format(urn, action),
        }

        url = 'http://{}:{}/{}'.format(self.__host, self.__port, url)

        g_logger.debug("Sending request to %s: with headers : %s and body : %s", url, headers, soap_body)
        req = Request(url, soap_body, headers)

        try:
            res = urlopen(req, timeout=self.__timeout).read()
        except HTTPError as e:
            g_logger.fatal(str(e))
            raise UserControlException("This command has failed, maybe the TV does not support it.")
        except (socket.error, socket.timeout, URLError) as e:
            g_logger.fatal(str(e))
            raise RemoteControlException("The TV is unreacheable.")
        g_logger.debug("Receveid response: %s", res)
        return res

    def send_key(self, key):
        """Send a key command to the TV.

        @param [str] key a predefined keys from Keys enum
        """
        if isinstance(key, Keys):
            key = key.value
        params = '<X_KeyEvent>{}</X_KeyEvent>'.format(key)
        g_logger.info("Send Key %s to %s", key, self.__host)
        self.soap_request(URL_CONTROL_NRC, URN_REMOTE_CONTROL,
                          'X_SendKey', params)

    def get_volume(self):
        """Return the current volume level.

        @return [int] the volume value
        """
        params = '<InstanceID>0</InstanceID><Channel>Master</Channel>'
        g_logger.info("Send GetVolume request to %s", self.__host)
        res = self.soap_request(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                                'GetVolume', params)
        root = xml_elm.fromstring(res)
        el_volume = root.find('.//CurrentVolume')
        return int(el_volume.text)

    def set_volume(self, volume):
        """Set a new volume level

        @param [int] the new value for volume
        """
        if volume > 100 or volume < 0:
            raise Exception('Bad request to volume control. '
                            'Must be between 0 and 100')
        params = ('<InstanceID>0</InstanceID><Channel>Master</Channel>'
                  '<DesiredVolume>{}</DesiredVolume>').format(volume)
        g_logger.info("Send SetVolume request to %s", self.__host)
        self.soap_request(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                          'SetVolume', params)

    def get_mute(self):
        """Return if the TV is muted

        @return [bool] the mute status
        """
        params = '<InstanceID>0</InstanceID><Channel>Master</Channel>'
        g_logger.info("Send GetMute request to %s", self.__host)
        res = self.soap_request(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                                'GetMute', params)
        root = xml_elm.fromstring(res)
        el_mute = root.find('.//CurrentMute')
        return el_mute.text != '0'

    def set_mute(self, enable):
        """Mute or unmute the TV.

        @param [bool] true if mute must be enabled, false if not
        """
        data = '1' if enable else '0'
        params = ('<InstanceID>0</InstanceID><Channel>Master</Channel>'
                  '<DesiredMute>{}</DesiredMute>').format(data)
        g_logger.info("Send SetMute request to %s", self.__host)
        self.soap_request(URL_CONTROL_DMR, URN_RENDERING_CONTROL,
                          'SetMute', params)
