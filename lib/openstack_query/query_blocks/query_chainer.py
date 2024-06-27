from typing import Tuple, List, Optional, Union, Dict

from custom_types.openstack_query.aliases import PropValue
from enums.cloud_domains import CloudDomains
from enums.query.props.prop_enum import PropEnum
from enums.query.query_presets import QueryPresetsGeneric
from enums.query.query_types import QueryTypes
from exceptions.query_chaining_error import QueryChainingError


class QueryChainer:
    """
    Helper class to handle chaining queries together
    """

    def __init__(self, chain_mappings):
        self._chain_mappings = chain_mappings

        self._forwarded_values: Optional[Dict[PropValue, List[Dict]]] = None
        self._link_prop: Optional[PropEnum] = None

    @property
    def forwarded_info(self) -> Optional[Tuple[PropEnum, Dict]]:
        """
        return forwarded info, a tuple of link prop and grouped results to forward
        """
        return self._link_prop, self._forwarded_values

    def set_forwarded_vals(
        self, prop: PropEnum, forwarded_values: Dict[PropValue, List[Dict]]
    ):
        """
        a setter which sets forwarded_values and shared prop for chaining
        :param prop: shared common property which is used to get prop val from this query openstack objects that will
        be used to apply given forwarded properties to results
        :param forwarded_values: a set of outputs generated from a previous query to forward on to this query.
        Output is grouped by a shared common property
        """
        self._forwarded_values = forwarded_values
        self._link_prop = prop

    def get_chaining_props(self) -> List[QueryTypes]:
        """
        Gets a list of all supported props that can be used to chain to other queries
        """
        return list(self._chain_mappings.keys())

    def check_prop_supported(self, prop: PropEnum) -> bool:
        """
        Checks whether a prop can be used as a link prop for the query
        :param prop: prop to check if it is a chain prop for given query
        """
        return prop in self._chain_mappings.keys()

    def get_link_props(
        self, next_query: QueryTypes
    ) -> Optional[Tuple[PropEnum, PropEnum]]:
        """
        Get the link property pair to use to convert from current query to new query
        (if mapping exists)
        :param next_query: next Query QueryTypes
        """

        new_query_props = next_query.value.get_prop_mapping()
        for start_chain_prop, check_prop in self._chain_mappings.items():
            if check_prop in new_query_props:
                return start_chain_prop, check_prop
        return None

    @staticmethod
    def parse_then(
        current_query,
        query_type: Union[str, QueryTypes],
        keep_previous_results: bool = False,
    ):
        """
        Public static method to chain current query into another query of a different type
        and return the new query so that it will work only on the results of the original query.
        :param current_query: current QueryAPI object
        :param query_type: an enum representing the new query to chain into
        :param keep_previous_results: boolean that if true - will forward outputs from
        this query (and previous chained queries) onto new query.
        """

        # prevents circular imports
        # pylint:disable=import-outside-toplevel
        from openstack_query.query_factory import QueryFactory
        from openstack_query.api.query_api import QueryAPI

        if isinstance(query_type, str):
            query_type = QueryTypes.from_string(query_type)

        link_props = current_query.chainer.get_link_props(query_type)
        if not link_props:
            raise QueryChainingError(
                f"Query Chaining Error: Could not find a way to chain current query into {query_type}"
            )

        if not current_query.to_props():
            raise QueryChainingError(
                "Query Chaining Error: No values found after running this query - aborting. "
                "Have you run the query first?"
            )

        # remove user-defined parsing
        prev_selected_props = current_query.output.selected_props
        prev_grouping = current_query.parser.grouper
        current_query.parser.group_by = None

        # grab all link prop values - including duplicates
        search_values = current_query.select([link_props[0]]).to_props(flatten=True)[
            link_props[0].name.lower()
        ]

        # re-configure user-defined parsing
        current_query.parser.grouper = prev_grouping
        current_query.output.selected_props = prev_selected_props

        new_query = QueryAPI(QueryFactory.build_query_deps(query_type.value))

        if keep_previous_results:
            # store forwarded results and link prop in new query
            new_query.chainer.set_forwarded_vals(
                link_props[1],
                current_query.group_by(link_props[0]).to_props(),
            )

        return new_query.where(
            QueryPresetsGeneric.ANY_IN,
            link_props[1],
            values=search_values,
        )

    @staticmethod
    def run_append_from_query(
        current_query,
        query_type: Union[str, QueryTypes],
        cloud_account: Union[str, CloudDomains],
        props: List[PropEnum],
    ):
        """
        Public static method to run query from an append_from call - and return result
        :param current_query: current QueryAPI object
        :param query_type: an enum representing the new query we want to append properties from
        :param cloud_account: A String or a CloudDomains Enum for the clouds configuration to use
        :param props: one or more properties to collect described as enum
        """
        if isinstance(query_type, str):
            query_type = QueryTypes.from_string(query_type)

        new_query = current_query.then(query_type, keep_previous_results=False)
        new_query.select(props)
        new_query.run(cloud_account)

        link_props = current_query.chainer.get_link_props(query_type)
        return link_props[0], new_query.group_by(link_props[1]).to_props()
