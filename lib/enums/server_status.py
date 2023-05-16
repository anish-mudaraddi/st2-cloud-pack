from enum import auto

from enums.auto_name import _AutoName


# pylint: disable=too-few-public-methods
class ServerStatus(_AutoName):
    """
    Holds a list of statuses for which a server can be in
    """

    SUSPENDED = auto()
    ACTIVE = auto()
    SHUTOFF = auto()
    ERROR = auto()

    @staticmethod
    def from_string(val: str):
        """
        Converts a given string in a case-insensitive way to the enum values
        """
        return ServerStatus[val.upper()]
