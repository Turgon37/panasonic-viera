# -*- coding: utf8 -*-


class RemoteControlException(Exception):
    """Exception for network remote controls errors
    """
    pass

class UserControlException(RemoteControlException):
    """Exceptions for users usage errors
    """
    pass
