from typing import Union, List, Dict, Callable
from enums.query.props.prop_enum import PropEnum
from exceptions.query_chaining_error import QueryChainingError
from openstack_query.query_blocks.result import Result
from custom_types.openstack_query.aliases import OpenstackResourceObj, PropValue


class ResultsContainer:
    """
    Helper class to manage a list of query results as Result objects
    """

    DEFAULT_OUT = "Not Found"

    def __init__(self, prop_enum_cls):
        self._prop_enum_cls = prop_enum_cls
        self._results: List = []
        self._parsed_results: Union[List, Dict] = []

    def to_props(self, *props: PropEnum) -> Union[Dict, List]:
        """
        Output the stored results, only outputting the properties given
        :props: A set of prop enums to select
        """
        results = self._parsed_results or self._results
        if not results:
            return []

        if isinstance(results, list):
            return [item.as_props(*props) for item in results]
        return {
            name: [item.as_props(*props) for item in group]
            for name, group in results.items()
        }

    def to_objects(self) -> Union[Dict, List]:
        """
        Output the results stored - as openstack objects
        """

        results = self._parsed_results or self._results
        if not results:
            return []

        if isinstance(results, list):
            return [item.as_object() for item in results]
        return {
            name: [item.as_object() for item in group]
            for name, group in results.items()
        }

    def store_query_results(self, query_results: List[OpenstackResourceObj]):
        """
        a setter to set results after running the query with query results
        :param query_results: A list of openstack objects returned after running query
        """
        self._results = [
            Result(self._prop_enum_cls, item, self.DEFAULT_OUT)
            for item in query_results
        ]

    def apply_forwarded_results(
        self,
        link_prop: PropEnum,
        forwarded_results: Dict[PropValue, List[Dict]],
    ):
        """
        public method that when called will add appropriate forwarded result entry onto each result.
        (expects results to be a list)
        :param forwarded_results: A set of grouped results forwarded from a previous query to attach to results
        :param link_prop: An prop enum that the forwarded results are grouped by
        """

        if not self._results:
            raise QueryChainingError(
                "Query Chaining Error: Could not apply then() or append_from()."
                "Either run() hasn't been called yet or run() returns no results"
            )

        for item in self._results:
            prop_val = item.get_prop(link_prop)

            # NOTE: This mutates forwarded_results
            forwarded_result = self._get_forwarded_result(prop_val, forwarded_results)

            item.update_forwarded_properties(forwarded_result)

    @staticmethod
    def _get_forwarded_result(
        prop_val: str, forwarded_results: Dict[str, List]
    ) -> Dict:
        """
        static helper method to return forwarded values that match a given property value. Used for chaining
        This handles two chaining cases:
            - many-to-one (or one-to-one as we're using duplicates)
                - where multiple forwarded outputs maps to one openstack object in result
                - the result will contain exact number of duplicate openstack objects so each forwarded output is
                assigned to an appropriate copy

            - one-to-many - where one forwarded output needs to map to multiple openstack objects in results

        :param prop_val: common property value to use to find a set of forwarded values to return
        :param forwarded_results: a grouped dictionary which holds forwarded values grouped by common property value
        """

        if not forwarded_results:
            return {}

        result_to_attach = forwarded_results[prop_val][0]

        # if forwarded_results group contains only one item:
        #   - we assume we're chaining a one-to-many and keep at least one value

        # if it contains multiple item:
        #   - we assume many-to-one and delete the value

        # deleting is a nice way of making sure each value is set - otherwise we need to keep track
        # of the index position of last read item for each group
        if len(forwarded_results[prop_val]) > 1:
            del forwarded_results[prop_val][0]

        return result_to_attach

    def parse_results(self, parse_func: Callable[[List[Result]], Union[List]]):
        """
        This method applies a pre-set parse function which will sort and/or group the results
        :param parse_func: parse function
        """
        self._parsed_results = parse_func(self._results)
