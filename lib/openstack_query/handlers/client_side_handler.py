import logging
import inspect
from typing import Optional, Tuple, Any

from openstack_query.handlers.handler_base import HandlerBase
from custom_types.openstack_query.aliases import (
    FilterFunc,
    PresetPropMappings,
    ClientSideFilterFunc,
    PropFunc,
    FilterParams,
    OpenstackResourceObj,
)

from enums.query.query_presets import QueryPresets
from enums.query.props.prop_enum import PropEnum
from exceptions.query_preset_mapping_error import QueryPresetMappingError

logger = logging.getLogger(__name__)


class ClientSideHandler(HandlerBase):
    """
    Base class for subclasses that handle client-side filtering.
    This class stores a dictionary which maps preset/property pairs to a filter function that will be used after
    listing openstack resources
    """

    def __init__(self, filter_func_mappings: PresetPropMappings):
        self._filter_function_mappings = filter_func_mappings

    def check_supported(self, preset: QueryPresets, prop: PropEnum) -> bool:
        """
        Method that returns True if filter function exists for a preset-property pair
        :param preset: A QueryPreset Enum for which a client-side filter function mapping may exist for
        :param prop: A property Enum for which a client-side filter function mapping may exist for
        """
        if not self.preset_known(preset):
            return False

        if prop in self._filter_function_mappings[preset]:
            return True

        # '*' represents that all props are valid for preset
        if ["*"] == self._filter_function_mappings[preset]:
            return True

        return False

    def preset_known(self, preset: QueryPresets) -> bool:
        """
        Method that returns True if a preset is known to the handler
        :param preset: A QueryPreset Enum which may have filter function mappings known to the handler
        """
        return preset in self._filter_function_mappings.keys()

    def get_filter_func(
        self,
        preset: QueryPresets,
        prop: PropEnum,
        prop_func: PropFunc,
        filter_func_kwargs: Optional[FilterParams] = None,
    ) -> Optional[ClientSideFilterFunc]:
        """
        Method that checks and returns a parsed filter function (if a mapping exists in this handler).
        the parsed filter function will take as input a single openstack resource and return
        True if resources passes check, False if not.

        :param preset: A QueryPreset Enum for which a filter function mapping may exist for
        :param prop: A property Enum for which a filter function mapping may exist for
        :param prop_func: A function to get a property of an openstack resource when given it as input
        :param filter_func_kwargs: A dictionary of keyword: argument pairs to pass into filter function
        """

        filter_func = None
        if self.check_supported(preset, prop):
            filter_func = self._filter_functions.get(preset, None)

        if not filter_func:
            logger.error(
                "Error: If you are here as a developer - "
                "you have likely not forgotten to add a mapping for the preset %s and property %s pair.\n"
                "\t- check the _get_client_side_handlers in <Resource>Query class",
                preset.name,
                prop.name,
            )

            logger.error(
                "Error: If you are here as a user - "
                "double check whether the preset %s is compatible with the property %s you're querying by.\n"
                "\t- i.e. using LESS_THAN on User property USER_NAME will not work since USER_NAME property "
                "is not an integer.\n"
                "\t- however, if you believe the preset should be compatible with the property please raise an "
                "issue with the repo maintainer",
                preset.name,
                prop.name,
            )

            raise QueryPresetMappingError(
                "Preset Not Found: failed to find filter_function mapping for preset "
                f"'{preset.name}' and property '{prop.name}'"
                "does the preset work with property specified?"
            )

        logger.debug(
            "found client-side filter function '%s' for preset %s: prop %s pair",
            filter_func.__name__,
            preset.name,
            prop.name,
        )

        filter_func_valid, reason = self._check_filter_func(
            filter_func, filter_func_kwargs
        )
        if not filter_func_valid:
            raise QueryPresetMappingError(
                "Preset Argument Error: failed to build client-side filter function for preset:prop: "
                f"'{preset.name}':'{prop.name}' "
                f"reason: {reason}"
            )

        return lambda resource: self._filter_func_wrapper(
            resource, filter_func, prop_func, filter_func_kwargs
        )

    @staticmethod
    def _filter_func_wrapper(
        item: OpenstackResourceObj,
        selected_filter_func: FilterFunc,
        selected_prop_func: PropFunc,
        filter_func_kwargs: Optional[FilterParams] = None,
    ) -> bool:
        """
        Method that acts as a wrapper to a filter function, if the property cannot be found for the resource
        we return False before calling the filter function - since there's no property to compare.
        :param item: An openstack resource item
        :param selected_filter_func: The selected filter function to run if property given can be retrieved from
        given openstack resource
        :param selected_prop_func: The selected prop function to run to get property from given openstack resource
        :param **filter_func_kwargs: A dictionary of keyword args to configure selected filter function
        """
        try:
            item_prop = selected_prop_func(item)
        except AttributeError:
            return False
        if filter_func_kwargs:
            return selected_filter_func(item_prop, **filter_func_kwargs)
        return selected_filter_func(item_prop)

    @staticmethod
    def _check_filter_func(
        func: FilterFunc, func_kwargs: Optional[FilterParams] = None
    ) -> Tuple[bool, str]:
        """
        Method that checks a given function can accept a set of kwargs as arguments.
        :param func: function to test
        :param func_kwargs: kwargs to test
        """

        signature = inspect.signature(func)

        # skip first parameter for the filter function as this is always the a positional arg which takes
        # an Openstack resource property as the input for our filter function to compare against
        parameters = list(signature.parameters.values())[1:]

        has_varargs = any(param.kind == param.VAR_POSITIONAL for param in parameters)
        has_varkwargs = any(param.kind == param.VAR_KEYWORD for param in parameters)

        logger.debug(
            "checking client-side filter function against provided parameters\n\t%s",
            "\n\t".join([f"{key}: '{value}'" for key, value in func_kwargs.items()]),
        )

        all_params = [param.name for param in parameters]
        log_all_params = "<none>"
        if all_params:
            log_all_params = "\n\t".join(all_params)
        logger.debug(
            "client-side filter function '%s' has the following params:\n\t%s",
            func.__name__,
            log_all_params,
        )

        req_params = [
            param.name
            for param in parameters
            if param.VAR_POSITIONAL and param.default == inspect.Parameter.empty
        ]
        log_all_req_params = "<none>"
        if req_params:
            log_all_req_params = "\n\t".join(req_params)

        logger.debug(
            "of those, the following params are required:\n\t%s", log_all_req_params
        )

        for param in parameters:
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                param_name = param.name
                if param_name in func_kwargs:
                    kwargs_value = func_kwargs[param_name]
                    param_type = param.annotation
                    if param_type not in [
                        Any,
                        inspect.Parameter.empty,
                    ] and not isinstance(kwargs_value, param_type):
                        return (
                            False,
                            f"{param_name} given has incorrect type, "
                            f"expected {param_type}, found {type(kwargs_value)}",
                        )
                elif param.default is inspect.Parameter.empty:
                    return False, f"{param_name} expected but not given"

        if not has_varargs and not has_varkwargs:
            # Check for extra items in kwargs not present in the function signature
            unexpected_vals = set(func_kwargs.keys()) - set(p.name for p in parameters)
            if unexpected_vals:
                return False, f"unexpected arguments: '{unexpected_vals}'"
        return True, ""