import logging
import time
from abc import abstractmethod
from typing import Optional, List, Any, Dict, Callable

from custom_types.openstack_query.aliases import (
    PropFunc,
    ServerSideFilters,
    ClientSideFilters,
    OpenstackResourceObj,
    ClientSideFilterFunc,
)
from exceptions.parse_query_error import ParseQueryError
from openstack_api.openstack_connection import OpenstackConnection
from openstack_api.openstack_wrapper_base import OpenstackWrapperBase

logger = logging.getLogger(__name__)

# pylint:disable=too-few-public-methods


class RunnerWrapper(OpenstackWrapperBase):
    """
    Base class for Runner classes.
    Runner classes encapsulate running any openstacksdk commands
    """

    # Sets the limit for getting values from openstack
    _LIMIT_FOR_PAGINATION = 1000
    _PAGINATION_CALL_LIMIT = 1000
    RESOURCE_TYPE = type(None)

    def __init__(self, marker_prop_func: PropFunc, connection_cls=OpenstackConnection):
        OpenstackWrapperBase.__init__(self, connection_cls)
        self._page_marker_prop_func = marker_prop_func

    def run(
        self,
        cloud_account: str,
        client_side_filters: Optional[ClientSideFilters] = None,
        server_side_filters: Optional[ServerSideFilters] = None,
        from_subset: Optional[List[Any]] = None,
        **kwargs,
    ) -> List[OpenstackResourceObj]:
        """
        Public method that runs the query by querying openstacksdk and then applying a filter function.
        :param cloud_account: A string for the account from the clouds configuration to use
        :param client_side_filters: An Optional list of filter functions to run locally that we can use to limit the
        results after querying openstacksdk
        :param server_side_filters: An Optional list of filter kwargs to limit the results by when querying openstacksdk
        :param from_subset: A subset of openstack resources to run query on instead of querying openstacksdk
        :param kwargs: An extra set of kwargs to pass to internal _run_query method that changes what/how the
        openstacksdk query is run
            - valid kwargs to _run_query is specific to the runner object - see docstrings for _run_query() on the
            runner of interest.
        """

        if from_subset and server_side_filters:
            logger.error(
                "Error: Received server-side filters - suggesting that the query requires getting results via "
                "openstacksdk, but you've also provided openstack objects directly - suggesting that you want to filter"
                "a set already given. Not sure what to do - aborting."
            )
            raise RuntimeError(
                "Ambiguous Query: received both server-side filters and values passed directly using 'from_subset'"
            )

        logger.debug("making connection to openstack")
        start = time.time()

        if from_subset:
            logger.info("'from_subset' run() param given - running query on subset")
            resource_objects = self._parse_subset(
                subset=from_subset,
            )
            logger.debug(
                "subset parsed. (time elapsed: %0.4f seconds)", time.time() - start
            )
        else:
            logger.info("running query using openstacksdk and server-side filters")
            with self._connection_cls(cloud_account) as conn:
                logger.debug(
                    "openstack connection established - using cloud account '%s'",
                    cloud_account,
                )
                resource_objects = self._run_with_openstacksdk(
                    conn=conn, server_filters=server_side_filters, **kwargs
                )
            logger.debug(
                "server-side quer(y/ies) completed - found %s items. (time elapsed: %0.4f seconds)",
                len(resource_objects),
                time.time() - start,
            )

        logger.info("applying client side filters - if any")
        if client_side_filters:
            resource_objects = self._apply_client_side_filters(
                items=resource_objects, filters=client_side_filters
            )

        logger.info(
            "Query Complete! Found %s items. Time elapsed: %0.4f seconds",
            len(resource_objects),
            time.time() - start,
        )
        return resource_objects

    def _run_with_openstacksdk(
        self,
        conn: OpenstackConnection,
        server_filters: Optional[ServerSideFilters] = None,
        **kwargs,
    ):
        if not server_filters:
            server_filters = [None]

        kwargs = self._parse_meta_params(conn, **kwargs)
        meta_param_log_str = "\n\t\t".join(
            [f"{key}: '{val}'" for key, val in kwargs.items()]
        )
        logger.info("found %s set(s) of server-side filters", len(server_filters))
        resource_objects = []
        for i, query_filters in enumerate(server_filters, 1):
            logger.debug("running query %s / %s", i, len(server_filters))

            filters_log_str = "None (getting all)"
            if query_filters:
                filters_log_str = "\n\t".join(
                    [f"{key}: '{val}'" for key, val in query_filters.items()]
                )

            logger.debug(
                "Running OpenstackSDK Query with: "
                "\n\tserver side filters: "
                "\n%s "
                "\n\n run() kwargs: "
                "\n\t%s",
                filters_log_str,
                "None" if not meta_param_log_str else meta_param_log_str,
            )

            resource_objects.extend(self._run_query(conn, query_filters, **kwargs))

        return resource_objects

    def _run_paginated_query(
        self,
        paginated_call: Callable,
        server_side_filters: Optional[ServerSideFilters] = None,
    ):
        """
        Helper method for running a query using pagination - openstacksdk calls usually return a maximum number of
        values - (set by limit) and to continue getting values we can pass a "marker" value of the last item seen to
        continue the query - this speeds up the time needed to run queries
        :param paginated_call: A lambda function which takes a openstacksdk call which allows limit and marker to be set
        :param server_side_filters: A set of filters to pass to openstacksdk call
        """

        paginated_filters = {"limit": self._LIMIT_FOR_PAGINATION, "marker": None}
        paginated_filters.update(server_side_filters)
        query_res = []

        curr_marker = None
        num_calls = 1
        while True:
            logger.debug("starting page loop, completed %s loops", num_calls)
            num_calls += 1
            if num_calls > self._PAGINATION_CALL_LIMIT:
                logger.warning(
                    "max page loops reached %s - terminating early", num_calls
                )
                break

            prev = None
            for i, resource in enumerate(paginated_call(**paginated_filters)):
                # Workaround for Endless loop error detected if querying for stfc users (via ldap)
                # for loop doesn't seem to terminate - and outputs the same value when given "limit" and "marker"
                if prev == resource:
                    logger.warning(
                        "duplicate entries found, likely an endless page loop - terminating early"
                    )
                    break

                query_res.append(resource)
                # openstacksdk calls break after going over pagination limit
                if i == self._LIMIT_FOR_PAGINATION - 1:
                    # restart the for loop with marker set
                    paginated_filters.update(
                        {"marker": self._page_marker_prop_func(resource)}
                    )
                    logger.debug(
                        "page limit reached: %s - setting new marker: %s",
                        self._LIMIT_FOR_PAGINATION,
                        paginated_filters["marker"],
                    )
                    break

                prev = resource

            # if marker hasn't changed, then has query terminated
            if not paginated_filters or paginated_filters["marker"] == curr_marker:
                logger.debug("page loop terminated")
                break
            # set marker as current
            curr_marker = paginated_filters["marker"]
        return query_res

    def _apply_client_side_filters(
        self, items: List[OpenstackResourceObj], filters: ClientSideFilters
    ) -> List[OpenstackResourceObj]:
        """
        Removes items from a list by running a given filter functions
        :param items: List of items to query e.g. list of servers
        :param filters: filter functions that we can use to limit the results after querying openstacksdk,
            - each function takes an openstack resource object and returns True if it passes the filter, false if not
        :return: List of items that match the1 given query
        """
        for client_filter in filters:
            items = self._apply_client_side_filter(items, client_filter)
        return items

    @staticmethod
    def _apply_client_side_filter(
        items: List[OpenstackResourceObj], client_filter: ClientSideFilterFunc
    ) -> Optional[List[OpenstackResourceObj]]:
        """
        Method that will apply a client filter on a list of openstack items
        :param items: A list of openstack resources
        :param client_filter: A client filter to apply
        """
        return [item for item in items if client_filter(item) is True]

    @abstractmethod
    def _run_query(
        self,
        conn: OpenstackConnection,
        filter_kwargs: Optional[ServerSideFilters] = None,
        **kwargs,
    ) -> List[OpenstackResourceObj]:
        """
        This method runs the query by utilising openstacksdk commands. It will set get a list of all available
        resources in question and returns them
        :param conn: An OpenstackConnection object - used to connect to openstacksdk
        :param filter_kwargs: An Optional set of filter kwargs to limit the results by when querying openstacksdk
        :param kwargs: An extra set of run() params to pass to internal _run_query method that changes what/how the
        openstacksdk query is run - these kwargs are specific to the resource runner.
        """

    def _parse_subset(
        self, subset: List[OpenstackResourceObj]
    ) -> List[OpenstackResourceObj]:
        """
        This method is a helper function that will check a subset of openstack objects and check their validity
        :param _: An OpenstackConnection object - not used right now
        :param subset: A list of openstack objects to parse
        """

        # connection object may need to be used if we want to run validation checks
        if any(not isinstance(i, self.RESOURCE_TYPE) for i in subset):
            raise ParseQueryError(
                f"'from_subset' only accepts openstack objects of type {self.RESOURCE_TYPE}"
            )
        return subset

    @abstractmethod
    def _parse_meta_params(self, conn: OpenstackConnection, **kwargs) -> Dict[str, str]:
        """
        This method is a helper function that will parse a set of meta params (run params) specific to the resource and
        return a set of parsed meta-params to pass to _run_query
        """
