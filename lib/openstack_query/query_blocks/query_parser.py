from typing import List, Dict, Tuple, Union, Optional, Type
import logging
from collections import OrderedDict
from enums.query.props.prop_enum import PropEnum
from enums.query.sort_order import SortOrder
from custom_types.openstack_query.aliases import (
    OpenstackResourceObj,
    PropValue,
    GroupMappings,
    GroupRanges,
)
from exceptions.parse_query_error import ParseQueryError

logger = logging.getLogger(__name__)


class QueryParser:
    """
    Helper class for taking query output and parsing it into a format which can then be outputted.
    Performs any sorting / grouping the user has specified
    """

    def __init__(self, prop_enum_cls: Type[PropEnum]):
        self._prop_enum_cls = prop_enum_cls
        self._sort_by = {}
        self._group_by = None
        self._group_mappings = {}

    @property
    def group_by(self):
        """
        a getter method to return group_by prop enum
        """
        return self._group_by

    @group_by.setter
    def group_by(self, prop: PropEnum):
        """
        a setter method to set group_by prop enum
        :param prop: prop enum to group by
        """
        self._group_by = prop

    @property
    def sort_by(self):
        """
        a getter method to return sort_by options
        """
        return self._sort_by

    @sort_by.setter
    def sort_by(self, sort_by: Dict[PropEnum, bool]):
        """
        a setter method to set sort_by options
        :param sort_by: a dictionary of prop enum to sort by mapped to order
        (True for Descending, False of Ascending)
        """
        self._sort_by = sort_by

    @property
    def group_mappings(self):
        """
        a getter method to set group_mappings options
        """
        return self._group_mappings

    @group_mappings.setter
    def group_mappings(self, group_mappings: GroupMappings):
        """
        a setter method to set group_mapping options
        :param group_mappings: a dictionary of group name to a list of
        property values that belong to that group
        """
        self._group_mappings = group_mappings

    def reset(self):
        """
        Method which resets pre-configured grouping and sorting attributes
        """
        self.group_by = None
        self.group_mappings = {}
        self.sort_by = {}

    def parse_sort_by(self, *sort_by: Tuple[PropEnum, SortOrder]) -> None:
        """
        Public method used to configure sorting results
        :param sort_by: one or more tuples of property name to sort by and order enum
        """
        sort_by_dict = {}
        for user_selected_prop, _ in sort_by:
            if user_selected_prop not in self._prop_enum_cls:
                raise ParseQueryError(
                    f"Error: Given property to sort by: {user_selected_prop.name} is not supported by query"
                )

        for prop, order in sort_by:
            order_log_str = "DESC" if order.value else "ASC"
            logging.debug(
                "adding sorting params: %s, order: %s", prop.name, order_log_str
            )
            sort_by_dict.update({prop: order.value})

        self.sort_by = sort_by_dict

        logging.debug(
            "sort params: %s",
            "\n\t".join(
                f"{prop}, order: {'DESC' if order else 'ASC'}"
                for prop, order in self.sort_by.items()
            ),
        )

    def parse_group_by(
        self,
        group_by: PropEnum,
        group_ranges: Optional[GroupRanges] = None,
        include_missing: Optional[bool] = False,
    ) -> None:
        """
        Public method used to configure grouping results.
        :param group_by: name of the property to group by
        :param group_ranges: a dictionary containing names of the group and list of prop values
        to select for that group
        :param include_missing: a flag which if set includes an extra grouping for values
        that don't fall into any group specified in group_ranges
        """

        if group_by not in self._prop_enum_cls:
            raise ParseQueryError(
                f"Error: Given property to group by: {group_by.name} is not supported by query"
            )

        self.group_by = group_by
        self.group_mappings = {}
        if group_ranges:
            self._parse_group_ranges(group_ranges)

        if include_missing:
            self._add_include_missing_group(group_ranges)

    def _parse_group_ranges(self, group_ranges: Optional[Dict[str, List[PropValue]]]):
        """
        helper method for parsing group ranges
        :param group_ranges: a dictionary containing names of the group and list of prop values
        to select for that group
        """
        logger.debug("creating filter functions for specified group ranges")
        prop_func = self._prop_enum_cls.get_prop_mapping(self.group_by)
        for name, prop_list in group_ranges.items():
            group_vals = tuple(prop_list)
            self.group_mappings[name] = (
                lambda obj, lst=group_vals: prop_func(obj) in lst
            )

    def _add_include_missing_group(self, group_ranges: GroupRanges):
        """
        Helper method used to add an extra group for group_by which includes
        all resource values not already included in any defined mappings
        :param group_ranges: A set of predefined group ranges to check against
        """
        # if ungrouped group wanted - filter for all not in any range specified
        all_prop_list = set()
        for _, prop_list in group_ranges.items():
            all_prop_list.update(set(prop_list))

        prop_func = self._prop_enum_cls.get_prop_mapping(self.group_by)
        logger.debug("creating filter function for ungrouped group")
        self.group_mappings["ungrouped results"] = (
            lambda obj: prop_func(obj) not in all_prop_list
        )

    def run_parser(
        self, obj_list: List[OpenstackResourceObj]
    ) -> Union[List[OpenstackResourceObj], Dict[str, List[OpenstackResourceObj]]]:
        """
        Public method used to parse query runner output - performs specified sorting and grouping
        :param obj_list: a list of openstack resource objects to parse
        """
        if not obj_list:
            return obj_list

        # we sort first - assuming sorting is commutative to grouping
        if self.sort_by:
            obj_list = self._run_sort(obj_list)

        if self.group_by:
            obj_list = self._run_group_by(obj_list)
        return obj_list

    def _run_sort(
        self,
        obj_list: List[OpenstackResourceObj],
    ) -> List[OpenstackResourceObj]:
        """
        method which sorts a list of openstack objects based on a dictionary of sort_by specs
        :param obj_list: A list of openstack objects to sort
            - descending - True, ascending - False
        """

        logger.debug("running multi-sort")
        sort_num = len(self.sort_by)
        for i, (sort_key, reverse) in enumerate(
            reversed(tuple(self.sort_by.items())), 1
        ):
            logger.debug("running sort %s / %s", i, sort_num)
            logger.debug("sorting by: %s, reverse=%s", sort_key, reverse)
            prop_func = self._prop_enum_cls.get_prop_mapping(sort_key)
            obj_list.sort(key=prop_func, reverse=reverse)
        return obj_list

    def _build_unique_val_groups(
        self,
        obj_list: List[OpenstackResourceObj],
    ) -> GroupMappings:
        """
        helper method to find all unique values for a given property in query results, and then,
        for each unique value, create a group mapping
        :param obj_list: A list of openstack objects to group
        """
        prop_func = self._prop_enum_cls.get_prop_mapping(self.group_by)
        # ordered dict to mimic ordered set
        # this is to preserve order we see unique values in - in case a sort has been done already
        unique_vals = OrderedDict({prop_func(obj): None for obj in obj_list})
        logger.debug(
            "unique values found %s - each will become a group",
            ",".join(f"{val}" for val in unique_vals),
        )

        group_mappings = {}

        # build groups
        for val in unique_vals.keys():
            group_key = val
            group_mappings[group_key] = (
                lambda obj, test_val=val: prop_func(obj) == test_val
            )

        return group_mappings

    def _run_group_by(
        self,
        obj_list: List[OpenstackResourceObj],
    ) -> Dict[str, List[OpenstackResourceObj]]:
        """
        helper method apply a set of group mappings onto a list of openstack objects. Returns a dictionary of grouped
        values where the key is the group name and value is a list of openstack objects that belong to that group
        :param obj_list: list of openstack objects to group
        """

        # if group mappings not specified - make a group for each unique value found for prop
        if not self.group_mappings:
            logger.info(
                "no group ranges specified - grouping by unique values of %s property",
                self.group_by.name,
            )
            self.group_mappings = self._build_unique_val_groups(obj_list)

        return {
            name: [item for item in obj_list if map_func(item)]
            for name, map_func in self.group_mappings.items()
        }
