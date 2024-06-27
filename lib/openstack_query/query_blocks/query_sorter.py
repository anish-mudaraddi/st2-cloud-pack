from typing import List, Tuple, Union
import logging

from openstack_query.query_blocks.result import Result

from enums.query.sort_order import SortOrder
from enums.query.props.prop_enum import PropEnum
from exceptions.parse_query_error import ParseQueryError

logger = logging.getLogger(__name__)


class QuerySorter:
    """
    Helper class for implementing sorting on query outputs
    """

    def __init__(self, prop_enum_cls):
        self._prop_enum_cls = prop_enum_cls
        self._sort_by = {}

    def _parse_sort_by_inputs(
        self, sort_by: List[Tuple[Union[PropEnum, str], Union[SortOrder, str]]]
    ) -> List[Tuple[PropEnum, SortOrder]]:
        """
        Converts list of sort_by() user inputs into Enums, any string aliases will be converted into Enums
        :param sort_by: one or more tuples of property Enum/String alias to sort by and order Enum/string alias
        """
        parsed_sort_by = []
        for prop, order in sort_by:
            if isinstance(prop, str):
                prop = self._prop_enum_cls.from_string(prop)
            if isinstance(order, str):
                order = SortOrder.from_string(order)
            parsed_sort_by.append((prop, order))
        return parsed_sort_by

    def parse_sort_by(
        self, sort_by: List[Tuple[Union[str, PropEnum], Union[str, SortOrder]]]
    ) -> None:
        """
        Public method used to configure sorting results
        :param sort_by: one or more tuples of property name to sort by and order enum
        """
        sort_by = self._parse_sort_by_inputs(sort_by)

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

            self._sort_by = sort_by_dict

            logging.debug(
                "sort params: %s",
                "\n\t".join(
                    f"{prop}, order: {'DESC' if order else 'ASC'}"
                    for prop, order in self._sort_by.items()
                ),
            )

    def run_sort_by(self, obj_list: List[Result]) -> List[Result]:
        """
        method which sorts a list of query results based on a dictionary of sort_by specs
        :param obj_list: a list of Result objects containing query results to sort
        """

        logger.debug("running multi-sort")
        sort_num = len(self._sort_by)
        obj_iter = enumerate(reversed(tuple(self._sort_by.items())), 1)
        for i, (sort_key, reverse) in obj_iter:
            logger.debug("running sort %s / %s", i, sort_num)
            logger.debug("sorting by: %s, reverse=%s", sort_key, reverse)
            prop_func = self._prop_enum_cls.get_prop_mapping(sort_key)
            obj_list.sort(
                key=lambda x, fn=prop_func: fn(x.as_object()), reverse=reverse
            )
        return obj_list
