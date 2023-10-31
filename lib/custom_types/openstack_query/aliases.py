from typing import List, Callable, Any, Dict, Union
from enums.query.props.prop_enum import PropEnum
from enums.query.query_presets import QueryPresets

from openstack.identity.v3.project import Project

PropValue = Union[str, bool, int]

# A type alias for a single openstack resource - i.e Server, Hypervisor etc
OpenstackResourceObj = Any

# A type alias for a Prop Func which takes an openstack resource and returns its corresponding property value
PropFunc = Callable[[OpenstackResourceObj], Any]

# A type alias for a dictionary which contains mappings between PropEnum and PropFunc
PropertyMappings = Dict[PropEnum, PropFunc]

# A type alias for a dictionary of params to pass to either client_side or server_side filters
FilterParams = Dict[str, Union[PropValue, List[PropValue]]]
FilterFunc = Callable[[PropFunc, FilterParams], bool]

# A type alias for a client-side filter func
ClientSideFilterFunc = Callable[[OpenstackResourceObj], bool]

# A type alias for a list of client-side filters to pass to run_query
ClientSideFilters = List[ClientSideFilterFunc]

# A type alias for a dictionary of filters to pass to openstacksdk commands as filter params
ServerSideFilter = Dict[str, PropValue]

# A type alias for representing a list of server-side-filters which will be used to run multiple openstacksdk commands
# - one command per server-side filter
ServerSideFilters = List[ServerSideFilter]

# A type alias for a function that takes a number of filter params and returns a set of server-side filters
ServerSideFilterFunc = Callable[
    [FilterParams], Union[ServerSideFilters, ServerSideFilter]
]

# type aliases for mapping server side filter functions to a corresponding preset-property pairs
PropToServerSideFilterFunc = Dict[PropEnum, ServerSideFilterFunc]
ServerSideFilterMappings = Dict[QueryPresets, PropToServerSideFilterFunc]

# type alias for mapping presets to valid properties that can be used with them
# can also accept a literal ['*'] to indicate preset works for all enum values
# NOTE: can't use Literal typing for ['*'] with python 3.6 so using generic List
PresetPropMappings = Dict[QueryPresets, Union[List, List[PropEnum]]]

# type alias for project identifier - either name/id or Project object
ProjectIdentifier = Union[str, Project]

# type alias for returning a query - any one of:
#   - A string with values in a tabulate table
#   - A list of Openstack Resource objects
#   - A list of dictionaries containing selected properties for each openstack resource
QueryReturn = Union[str, List[OpenstackResourceObj], List[Dict]]

# type alias for group mappings, a dictionary with group name as keys mapped to a function which takes
# an openstack resource object and returns a True if resource belongs to that group, False if not
GroupMappings = Dict[str, Callable[[OpenstackResourceObj], bool]]

# type alias for group ranges, a dictionary with group name as keys mapped to a list of prop values
# that should belong to that group
GroupRanges = Dict[str, List[PropValue]]


# a type alias for grouped and parsed outputs. A dicitonary of grouped prop-value as key and list of values
# that belong to that group
GroupedReturn = Dict[PropValue, List[Dict]]
