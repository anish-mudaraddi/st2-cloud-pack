from typing import Type
from openstack_query.api.query_api import QueryAPI
from openstack_query.mappings.mapping_interface import MappingInterface
from openstack_query.query_factory import QueryFactory
from openstack_query.mappings.user_mapping import UserMapping
from openstack_query.mappings.server_mapping import ServerMapping


def get_common(query_mapping: Type[MappingInterface]) -> QueryAPI:
    """
    helper function to create query object from given mapping class
    using QueryFactory
    :param query_mapping: a mapping class that defines property, runner and handler mappings
    """
    return QueryAPI(QueryFactory.build_query_deps(query_mapping))


# disable this so that we can write functions that mimic a query object
# pylint:disable=invalid-name


def ServerQuery() -> QueryAPI:
    """
    Simple helper function to setup a query using a factory
    """
    return get_common(ServerMapping)


def UserQuery() -> QueryAPI:
    """
    Simple helper function to setup a query using a factory
    """
    return get_common(UserMapping)
