from typing import Optional, Dict, Any, List
import logging

from openstack_query.handlers.client_side_handler import ClientSideHandler
from openstack_query.handlers.prop_handler import PropHandler
from openstack_query.handlers.server_side_handler import ServerSideHandler

from enums.query.query_presets import QueryPresets
from enums.query.props.prop_enum import PropEnum

from exceptions.parse_query_error import ParseQueryError
from exceptions.query_preset_mapping_error import QueryPresetMappingError
from exceptions.query_property_mapping_error import QueryPropertyMappingError

from custom_types.openstack_query.aliases import ClientSideFilterFunc, ServerSideFilters

logger = logging.getLogger(__name__)


class QueryBuilder:
    """
    Helper class to handle setting and validating query parameters - primarily parsing 'where()' arguments to get
    filter function or kwarg params to use when running query
    """

    def __init__(
        self,
        prop_handler: PropHandler,
        client_side_handlers: List[ClientSideHandler],
        server_side_handler: Optional[ServerSideHandler],
    ):
        self._client_side_handlers = client_side_handlers
        self._prop_handler = prop_handler
        self._server_side_handler = server_side_handler

        self._client_side_filter = None
        self._server_side_filters = None

    @property
    def client_side_filter(self) -> Optional[ClientSideFilterFunc]:
        """
        a getter method to return the client-side filter function
        """
        return self._client_side_filter

    @property
    def server_side_filters(self) -> Optional[ServerSideFilters]:
        """
        a getter method to return server-side filters to pass to openstacksdk
        """
        return self._server_side_filters

    def parse_where(
        self,
        preset: QueryPresets,
        prop: PropEnum,
        preset_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        method which parses and builds a filter function and (if possible) a set of openstack filter kwargs that
        corresponds to a given preset, property and set of preset arguments
        :param preset: Name of query preset to use
        :param prop: Name of property that the query preset will act on
        :param preset_kwargs: A set of arguments to pass to configure filter function and filter kwargs
        """

        if self._client_side_filter:
            logging.error(
                "Error: Chaining multiple where() functions currently not supported"
            )
            raise ParseQueryError("Error: Already set a query preset")

        prop_func = self._prop_handler.get_prop_func(prop)

        if not prop_func:
            logging.error(
                "Error: If you are here as a developer"
                "you have likely forgotten to add a prop mapping for the property '%s'"
                "under queries/<resource>_query",
                prop.name,
            )

            raise QueryPropertyMappingError(
                f"""
                Error: failed to get property mapping, given property
                {prop.name} is not supported in prop_handler
                """
            )

        preset_handler = self._get_preset_handler(preset, prop)
        self._client_side_filter = preset_handler.get_filter_func(
            preset=preset,
            prop=prop,
            prop_func=prop_func,
            filter_func_kwargs=preset_kwargs,
        )

        self._server_side_filters = self._server_side_handler.get_filters(
            preset=preset, prop=prop, params=preset_kwargs
        )
        if not self._server_side_filters:
            logger.info(
                "No server-side filters for preset '%s': prop '%s' pair "
                "- using client-side filter - this may take longer",
                preset.name,
                prop.name,
            )
        else:
            logger.info(
                "Found server-side filters for preset '%s': prop '%s' pair: '%s'",
                preset.name,
                prop.name,
                "\n\t".join(
                    [
                        f"{key}: '{val}'"
                        for key, val in self._server_side_filters.items()
                    ]
                ),
            )

    def _get_preset_handler(
        self, preset: QueryPresets, prop: PropEnum
    ) -> ClientSideHandler:
        """
        method which returns a preset handler object which supports the corresponding preset and property pair
        :param preset: A given preset that describes the query type
        :param prop: A prop which the preset will act on
        """

        # Most likely we have forgotten to add a mapping for a preset at the client-side
        # All presets should have a client-side handler associated to it
        if not any(i.preset_known(preset) for i in self._client_side_handlers):
            logger.error(
                "Error: If you are here as a developer "
                "you have likely not forgotten to instantiate a client-side handler for the "
                "preset '%s'",
                preset.name,
            )

            logger.error(
                "Error: If you are here as a user - double check whether the preset '%s' is compatible"
                "with the resource you're querying.\n "
                "i.e. using LESS_THAN for querying Users "
                "(as users holds no query-able properties which are of an integer type).\n "
                "However, if you believe it should please raise an issue with the repo maintainer"
            )

            raise QueryPresetMappingError(
                f"No client-side handler found for preset '{preset.name}' - property '{prop.name}' pair "
                f"- resource likely does not support querying using this preset"
            )

        for i in self._client_side_handlers:
            if i.check_supported(preset, prop):
                return i

        logger.error(
            "Error: if you are here as a developer"
            "you have likely forgotten to add client-side mappings for the preset '%s' "
            "under queries/<resource>_query",
            preset.name,
        )

        raise QueryPresetMappingError(
            f"No client-side handler found for preset '{preset.name}'"
            "- this query is likely misconfigured/preset is not supported on resource"
        )
