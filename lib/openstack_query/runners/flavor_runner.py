from typing import Optional, List
import logging

from openstack.compute.v2.flavor import Flavor
from openstack_api.openstack_connection import OpenstackConnection
from openstack_query.runners.runner_wrapper import RunnerWrapper

from custom_types.openstack_query.aliases import ServerSideFilters

logger = logging.getLogger(__name__)

# pylint:disable=too-few-public-methods


class FlavorRunner(RunnerWrapper):
    """
    Runner class for openstack flavor resource
    FlavorRunner encapsulates running any openstacksdk Flavor commands
    """

    RESOURCE_TYPE = Flavor

    def _parse_meta_params(self, _: OpenstackConnection, **__):
        logger.debug(
            "FlavorQuery doesn't take any extra run() parameters - ignoring any given"
        )
        return {}

    def _run_query(
        self,
        conn: OpenstackConnection,
        filter_kwargs: Optional[ServerSideFilters] = None,
        **_,
    ) -> List[Flavor]:
        """
        This method runs the query by running openstacksdk commands

        For FlavorQuery, this command finds all flavors that match a given set of filter_kwargs
        :param conn: An OpenstackConnection object - used to connect to openstacksdk
        :param filter_kwargs: An Optional list of filter kwargs to pass to conn.compute.flavors()
            to limit the flavors being returned.
            - see https://docs.openstack.org/api-ref/compute/#list-flavors-with-details
        """
        if not filter_kwargs:
            # return all info
            filter_kwargs = {"details": True}
        logger.debug(
            "running openstacksdk command conn.compute.flavors(%s)",
            ",".join(f"{key}={value}" for key, value in filter_kwargs.items()),
        )
        return self._run_paginated_query(conn.compute.flavors, filter_kwargs)
