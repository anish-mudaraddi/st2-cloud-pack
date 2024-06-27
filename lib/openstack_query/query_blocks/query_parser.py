from typing import List, Dict, Union, Type, Tuple, Optional
import logging

from custom_types.openstack_query.aliases import GroupRanges

from enums.query.sort_order import SortOrder
from enums.query.props.prop_enum import PropEnum

from openstack_query.query_blocks.query_grouper import QueryGrouper
from openstack_query.query_blocks.query_sorter import QuerySorter
from openstack_query.query_blocks.result import Result

logger = logging.getLogger(__name__)


class QueryParser:
    """
    Helper class for taking query output and parsing it into a format which can then be outputted.
    Performs any sorting / grouping the user has specified
    """

    def __init__(self, prop_enum_cls: Type[PropEnum]):
        self.sorter = QuerySorter(prop_enum_cls)
        self.grouper = QueryGrouper(prop_enum_cls)
        self._sort = False
        self._group = False

    def reset_group_by(self):
        self._group = False

    def parse_sort_by(
        self, sort_by: List[Tuple[Union[PropEnum, str], Union[SortOrder, str]]]
    ):
        """
        public method to set sorting parameters. Forwards onto sorter.parse_sort_by
        :param sort_by: one or more tuples of property name to sort by and order enum
        """
        self.sorter.parse_sort_by(sort_by)
        self._sort = True

    def parse_group_by(
        self,
        group_by: Union[str, PropEnum],
        group_ranges: Optional[GroupRanges] = None,
        include_missing: Optional[bool] = False,
    ):
        """
        public method to set grouping parameters. Forwards onto grouper.parse_group_by
        :param group_by: one or more tuples of property name to sort by and order enum
        :param group_ranges: a dictionary containing names of the group and list of prop values
        to select for that group
        :param include_missing: a flag which, if set, will include an extra grouping for values
        that don't fall into any group specified in group_ranges
        """
        self.grouper.parse_group_by(group_by, group_ranges, include_missing)
        self._group = True

    def run_parser(
        self, obj_list: List[Result]
    ) -> Union[List[Result], Dict[str, List[Result]]]:
        """
        Public method used to parse query runner output - performs specified sorting and grouping
        :param obj_list: a list of Result objects containing query results to parse
        (runs both sorting and grouping)
        """

        # we sort first - assuming sorting is commutative to grouping
        if self._sort:
            obj_list = self.sorter.run_sort_by(obj_list)

        if self._group:
            obj_list = self.grouper.run_group_by(obj_list)

        return obj_list
