from typing import List
import re
from custom_types.openstack_query.aliases import QueryReturn

from enums.query.query_presets import (
    QueryPresetsDateTime,
    QueryPresetsString,
    QueryPresetsGeneric,
)
from enums.query.props.server_properties import ServerProperties
from enums.cloud_domains import CloudDomains

from openstack_query.queries.server_query import ServerQuery
from openstack_query.managers.query_manager import QueryManager

from structs.query.query_preset_details import QueryPresetDetails
from structs.query.query_output_details import QueryOutputDetails

# pylint:disable=too-many-arguments


class ServerManager(QueryManager):
    """
    Manager for querying Openstack Server objects.
    """

    def __init__(self, cloud_account: CloudDomains):
        QueryManager.__init__(self, query=ServerQuery(), cloud_account=cloud_account)

    def search_all(self, **kwargs) -> QueryReturn:
        """
        method that returns a list of all servers
        :param kwargs: A set of optional kwargs to pass to the query
            - properties_to_select - list of strings representing which properties to select
            - output_type - string representing how to output the query
        """
        return self._build_and_run_query(
            preset_details=None,
            output_details=QueryOutputDetails.from_kwargs(
                prop_cls=ServerProperties, **kwargs
            ),
        )

    def search_by_datetime(
        self,
        search_mode: str,
        property_to_search_by: str,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        **kwargs,
    ) -> QueryReturn:
        """
        method that builds and runs a datetime-related query on Openstack Servers, and then returns results.
        Uses UTC timezone
        :param search_mode: A string representing what type of datetime query will be run - set as a Datetime Preset
        that the query will use
        :param property_to_search_by: A string representing a datetime property Enum that the preset will be used on
        - must be datetime compatible
        :param days: (Optional) Number of relative days in the past from now to use as threshold
        :param hours: (Optional) Number of relative hours in the past from now to use as threshold
        :param minutes: (Optional) Number of relative minutes in the past from now to use as threshold
        :param seconds: (Optional) Number of relative seconds in the past from now to use as threshold
        :param kwargs: A set of optional kwargs to pass to the query
            - properties_to_select - list of strings representing which properties to select
            - output_type - string representing how to output the query
        """
        preset_details = QueryPresetDetails(
            preset=QueryPresetsDateTime.from_string(search_mode),
            prop=ServerProperties.from_string(property_to_search_by),
            args={
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds": float(seconds),
            },
        )

        return self._build_and_run_query(
            preset_details=preset_details,
            output_details=QueryOutputDetails.from_kwargs(
                prop_cls=ServerProperties, **kwargs
            ),
        )

    def search_by_property(
        self, search_mode: str, property_to_search_by: str, values: List[str], **kwargs
    ) -> QueryReturn:
        """
        method that builds and runs a query to find Openstack servers with a selected property
        matching, or not matching given value(s)
        :param search_mode: A string representing a preset Enum ANY_IN or NOT_ANY_IN which dictates what query
        to perform
        if False - use the preset NOT_ANY_IN/NOT_EQUAL_TO
        :param property_to_search_by: A string representing a datetime property Enum that the preset will be used on
        :param values: A list of string values to compare server property against
        :param kwargs: A set of optional kwargs to pass to the query
            - properties_to_select - list of strings representing which properties to select
            - output_type - string representing how to output the query
        """
        args = {"values": values}
        preset = (
            QueryPresetsString.ANY_IN if search_mode else QueryPresetsString.NOT_ANY_IN
        )

        # If values contains only one value - use EQUAL_TO/NOT_EQUAL_TO as the preset instead to speed up query
        if len(values) == 1:
            equal_to_preset = {
                QueryPresetsString.ANY_IN: QueryPresetsGeneric.EQUAL_TO,
                QueryPresetsString.NOT_ANY_IN: QueryPresetsGeneric.NOT_EQUAL_TO,
            }.get(preset, None)
            if equal_to_preset:
                preset = equal_to_preset
                args = {"value": values[0]}

        return self._build_and_run_query(
            preset_details=QueryPresetDetails(
                preset=preset,
                prop=ServerProperties.from_string(property_to_search_by),
                args=args,
            ),
            output_details=QueryOutputDetails.from_kwargs(
                prop_cls=ServerProperties, **kwargs
            ),
        )

    def search_by_regex(self, property_to_search_by: str, pattern: str, **kwargs):
        """
        method that builds and runs a query to find Openstack servers with a selected property matching regex.
        :param property_to_search_by: A string representing a string property Enum that the preset will be used on
        :param pattern: A string representing a regex pattern
        :param kwargs: A set of optional kwargs to pass to the query
            - properties_to_select - list of strings representing which properties to select
            - output_type - string representing how to output the query
        """
        args = {"regex_string": re.compile(pattern)}

        return self._build_and_run_query(
            preset_details=QueryPresetDetails(
                preset=QueryPresetsString.MATCHES_REGEX,
                prop=ServerProperties.from_string(property_to_search_by),
                args=args,
            ),
            output_details=QueryOutputDetails.from_kwargs(
                prop_cls=ServerProperties, **kwargs
            ),
        )
