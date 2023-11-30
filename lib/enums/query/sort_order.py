from enum import Enum
from exceptions.parse_query_error import ParseQueryError


class SortOrder(Enum):
    """
    Enum class which holds enums for sort order. Used to specify sort order when
    querying and parsing query using sort_by
    """

    ASC = False
    DESC = True

    @staticmethod
    def from_string(val: str):
        """
        Converts a given string in a case-insensitive way to the enum values
        """
        try:
            return SortOrder[val.upper()]
        except KeyError as err:
            raise ParseQueryError(
                f"Could not find convert {val} into a sort order enum. "
                f"Available orders are {','.join([order.name for order in SortOrder])}"
            ) from err
