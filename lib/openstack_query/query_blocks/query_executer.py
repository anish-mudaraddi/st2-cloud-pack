import time
import logging
from typing import Tuple, Callable, Optional, Dict, List, Any, Union, Type

from openstack_query.runners.runner_wrapper import RunnerWrapper
from enums.cloud_domains import CloudDomains
from enums.query.props.prop_enum import PropEnum

from custom_types.openstack_query.aliases import (
    OpenstackResourceObj,
    ServerSideFilters,
    ClientSideFilters,
)

logger = logging.getLogger(__name__)


# pylint:disable=too-many-instance-attributes
# TODO: streamline these instance attributes later


class QueryExecuter:
    """
    Helper class to handle executing the query - primarily performing 'run()' method
    """

    def __init__(self, prop_enum_cls: Type[PropEnum], runner_cls: Type[RunnerWrapper]):
        self._prop_enum_cls = prop_enum_cls
        self.runner = runner_cls(self._prop_enum_cls.get_marker_prop_func())
        self._client_side_filters = None
        self._server_side_filters = None
        self._raw_results = []

    def reset(self):
        """
        Method which resets results attribute gained from running query
        """
        self.raw_results = []

    @property
    def client_side_filters(self):
        """
        a getter method to return the client-side filter function
        """
        return self._client_side_filters

    @client_side_filters.setter
    def client_side_filters(self, client_filters=ClientSideFilters):
        """
        Setter method for setting run filters
        :param client_filters: a list of filter functions that each take an openstack resource
        and returns True if it matches filter, False if not
        """
        self._client_side_filters = client_filters

    @property
    def server_side_filters(self):
        """
        a getter method to return the server side filter functions
        """
        return self._server_side_filters

    @server_side_filters.setter
    def server_side_filters(self, server_filters: ServerSideFilters):
        """
        a setter method to return the server side filter functions
        :param server_filters: A dictionary of filter kwargs to pass to openstacksdk
        """
        self._server_side_filters = server_filters

    @property
    def raw_results(self) -> List[OpenstackResourceObj]:
        """
        a getter for raw results
        """
        return self._raw_results

    @raw_results.setter
    def raw_results(self, results: List[OpenstackResourceObj]):
        """
        a setter for raw results
        """
        self._raw_results = results

    def run_query(
        self,
        cloud_account: Union[str, CloudDomains],
        from_subset: Optional[List[Any]] = None,
        **kwargs,
    ):
        """
        method that runs the query provided and outputs
        :param cloud_account: An Enum for the account from the clouds configuration to use
        :param from_subset: A subset of openstack resources to run query on instead of querying openstacksdk
        :param kwargs: An extra set of kwargs to pass to internal _run_query method that changes what/how the
        openstacksdk query is run
            - valid kwargs to _run_query is specific to the runner object - see docstrings for _run_query() on the
            runner of interest.
        """

        if isinstance(cloud_account, CloudDomains):
            cloud_account = cloud_account.name.lower()

        start = time.time()
        self.raw_results = self.runner.run(
            cloud_account=cloud_account,
            client_side_filters=self.client_side_filters,
            server_side_filters=self.server_side_filters,
            from_subset=from_subset,
            **kwargs,
        )
        logger.debug("run completed - time elapsed: %s seconds", time.time() - start)

    def parse_results(
        self,
        parse_func: Optional[Callable],
        output_func: Optional[Callable],
    ) -> Tuple[Union[List, Dict], Union[List, Dict]]:
        """
        This method takes the raw results computed in run_query() and applies the pre-set parser
        and generate output functions
        :param parse_func: function that groups and sorts raw results
        :param output_func: function that takes raw results and converts it into outputs
        """
        results = self.raw_results
        if parse_func:
            results = parse_func(results)
        return results, self.get_output(output_func, results)

    @staticmethod
    def get_output(
        output_func: Optional[Callable],
        results: Union[
            List[OpenstackResourceObj], Dict[str, List[OpenstackResourceObj]]
        ],
    ):
        """
        Helper method for getting the output using output func
        :param output_func: function that takes raw results and returns parsed outputs
        :param results: Either a list or group of Openstack Resource objects
        """
        if not output_func:
            return []

        if not isinstance(results, dict):
            return output_func(results)

        return {name: output_func(group) for name, group in results.items()}
