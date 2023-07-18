import re

from typing import List, Any, Pattern
from custom_types.openstack_query.aliases import PresetPropMappings

from enums.query.query_presets import QueryPresetsString
from openstack_query.handlers.client_side_handler import ClientSideHandler
from exceptions.missing_mandatory_param_error import MissingMandatoryParamError

# pylint: disable=too-few-public-methods


class ClientSideHandlerString(ClientSideHandler):
    """
    Client Side handler for String related queries.
    This class stores a dictionary which maps a String preset/prop pairs to a filter function
    Filter functions which map to QueryPresetsString are defined here
    """

    def __init__(self, filter_function_mappings: PresetPropMappings):
        super().__init__(filter_function_mappings)

        self._filter_functions = {
            QueryPresetsString.ANY_IN: self._prop_any_in,
            QueryPresetsString.MATCHES_REGEX: self._prop_matches_regex,
            QueryPresetsString.NOT_ANY_IN: self._prop_not_any_in,
        }

    def _prop_matches_regex(self, prop: Any, regex_string: Pattern[str]) -> bool:
        """
        Filter function which returns true if a prop matches a regex pattern
        :param prop: prop value to check against
        :param regex_string: a regex pattern to search with
        """
        return bool(re.match(regex_string, prop))

    def _prop_any_in(self, prop: Any, values: List[str]) -> bool:
        """
        Filter function which returns true if a prop matches any in a given list
        :param prop: prop value to check against
        :param values: a list of values to check against
        """
        if len(values) == 0:
            raise MissingMandatoryParamError(
                "values list must contain at least one item to match against"
            )
        return any(prop == val for val in values)

    def _prop_not_any_in(self, prop: Any, values: List[str]) -> bool:
        """
        Filter function which returns true if a prop does not match any in a given list
        :param prop: prop value to check against
        :param values: a list of values to check against
        """
        return not self._prop_any_in(prop, values)
