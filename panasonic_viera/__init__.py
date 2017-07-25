# -*- coding: utf8 -*-

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

"""
    This module provides a remote control client for Panasonic viera TVs

    Usage:

    >>> import panasonic_viera
    >>> rc = panasonic_viera.RemoteControl("192.168.1.2")
    >>> rc.sendKey(panasonic_viera.Keys.APPS)
    >>> rc.setVolume(30)
"""

import logging
import re
import sys

from .remote_control import RemoteControl
from .constants import Keys
from .utils import getLogger
from .exceptions import RemoteControlException, UserControlException

__version__ = '1.1.1'

__all__ = ['RemoteControl', 'Keys', 'getLogger',
    'RemoteControlException',
    'UserControlException']

def getOnlineVersion():
    """Fetch lib version from source repository
    """
    if sys.version_info[0] == 3:
        import urllib.request as urllib
    else:
        import urllib2 as urllib
    content = urllib.urlopen("https://raw.githubusercontent.com/Turgon37/panasonic-viera/master/panasonic_viera/__init__.py").read().decode()
    result = re.search('__version__\s=\s["\'](?P<version>[0-9]+\.[0-9]+\.[0-9]+)["\']', content)
    if result is not None:
        return result.group('version')
    return None
