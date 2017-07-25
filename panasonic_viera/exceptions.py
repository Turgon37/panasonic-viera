# -*- coding: utf8 -*-


class RemoteControlException(Exception):
    """Exception for network remote controls errors
    """

    def getCode(self):
        """Return the error code associated with this exception

        @return [int] code
        """
        if len(self.args) > 1:
            code = self.args[1]
            if hasattr(code, 'value'):
                return code.value
            else:
                return code

    def __str__(self):
        """Redefined the old behaviour with simple error
        """
        if len(self.args) > 0:
            return self.args[0]
        else:
            return super(RemoteControlException, self).__str__()

class UserControlException(RemoteControlException):
    """Exceptions for users usage errors
    """
    pass
