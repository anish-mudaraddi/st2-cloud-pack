from abc import abstractmethod
from enum import Enum
from typing import Optional
from custom_types.openstack_query.aliases import PropFunc


class PropEnum(Enum):
    """
    An enum base class for all openstack resource properties - for type annotation purposes
    """

    @staticmethod
    @abstractmethod
    def get_prop_func(prop) -> Optional[PropFunc]:
        """
        Method that returns the property function if function mapping exists for a given property Enum
        :param prop: A property Enum for which a function may exist for
        """

    @staticmethod
    @abstractmethod
    def get_marker_prop_func(self):
        """
        A getter method to return marker property function for pagination
        """
