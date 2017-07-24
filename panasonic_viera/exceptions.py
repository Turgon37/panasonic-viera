# -*- coding: utf8 -*-


class RemoteControlException(Exception):
    """Exception for network remote controls errors
    """

    def getCode(self):
        if len(self.args) > 1:
            code = self.args[1]
            if hasattr(code, 'value'):
                return code.value
            else:
                return code

class UserControlException(RemoteControlException):
    """Exceptions for users usage errors
    """
    pass
