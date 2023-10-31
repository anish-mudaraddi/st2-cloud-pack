from copy import deepcopy
from typing import List, Dict, Union, Type, Set, Optional
from tabulate import tabulate
from enums.query.props.prop_enum import PropEnum
from custom_types.openstack_query.aliases import (
    OpenstackResourceObj,
    PropValue,
    GroupedReturn,
)
from exceptions.query_chaining_error import QueryChainingError
from exceptions.parse_query_error import ParseQueryError


class QueryOutput:
    """
    Helper class for generating output for the query as a formatted table or selected properties - either as
    html or string

    TODO: Class should also handle grouping and sorting results
    """

    # what value to output if property is not found for an openstack object
    DEFAULT_OUT = "Not Found"

    def __init__(self, prop_enum_cls: Type[PropEnum]):
        self._prop_enum_cls = prop_enum_cls
        self._props = set()
        self._forwarded_outputs: Dict[PropEnum, GroupedReturn] = {}

    def update_forwarded_outputs(self, link_prop: PropEnum, values: Dict[str, List]):
        """
        method to set outputs to forward from other queries
        :param link_prop: the property that the results are grouped by
        :param values: grouped properties to forward
        """
        self._forwarded_outputs[link_prop] = values

    @property
    def forwarded_outputs(self) -> Dict[PropEnum, GroupedReturn]:
        """
        A getter for forwarded properties
        """
        return self._forwarded_outputs

    @property
    def selected_props(self) -> List[PropEnum]:
        """
        A getter for selected properties relevant to the query
        """
        if not self._props:
            return []
        return list(self._props)

    @selected_props.setter
    def selected_props(self, props=Set[PropEnum]):
        """
        A setter for setting selected properties
        :param props: A set of property enums to select for
        """
        self._props = props

    def reset(self):
        """
        Method which resets selected props
        """
        self.selected_props = set()

    def to_string(
        self,
        results: Union[List, Dict],
        title: str = None,
        groups: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        method to return results as a table
        :param results: a list of parsed query results - either a list or a dict of grouped results
        :param title: a title for the table(s) when it gets outputted
        :param groups: a list group to limit output by
        :param kwargs: kwargs to pass to _generate_table method
        """
        output = ""
        if title:
            output += f"{title}:\n"

        if isinstance(results, dict):
            if groups and any(group not in results.keys() for group in groups):
                raise ParseQueryError(
                    f"given group(s) {groups} not found - available groups {list(results.keys())}"
                )

            if not groups:
                groups = list(results.keys())

            for group_title in groups:
                group_list = results[group_title]
                output += self._generate_table(
                    group_list, return_html=False, title=f"{group_title}:\n", **kwargs
                )
        elif groups:
            raise ParseQueryError(
                f"Result is not grouped - cannot filter by given group(s) {groups}"
            )

        else:
            output += self._generate_table(
                results, return_html=False, title=None, **kwargs
            )
        return output

    def to_html(
        self,
        results: Union[List, Dict],
        title: str = None,
        groups: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        """
        method to return results as html table
        :param results: a list of parsed query results - either a list or a dict of grouped results
        :param title: a title for the table(s) when it gets outputted
        :param groups: a list group to limit output by
        :param kwargs: kwargs to pass to generate table
        """
        output = ""
        if title:
            output += f"<b> {title} </b><br/> "

        if isinstance(results, dict):
            if groups and any(group not in results.keys() for group in groups):
                raise ParseQueryError(
                    f"given group(s) {groups} not found - available groups {list(results.keys())}"
                )

            if not groups:
                groups = list(results.keys())

            for group_title in groups:
                group_list = results[group_title]
                output += self._generate_table(
                    group_list,
                    return_html=True,
                    title=f"<b> {group_title}: </b><br/> ",
                    **kwargs,
                )
        elif groups:
            raise ParseQueryError(
                f"Result is not grouped - cannot filter by given group(s) {groups}"
            )

        else:
            output += self._generate_table(
                results, return_html=True, title=None, **kwargs
            )
        return output

    def parse_select(self, *props: PropEnum, select_all=False) -> None:
        """
        Method which is used to set which properties to output once results are gathered
        This method checks that each Enum provided is valid and populates internal attribute which holds selected props
        :param select_all: boolean flag to select all valid properties
        :param props: any number of Enums representing properties to show
        """
        if select_all:
            self.selected_props = set(self._prop_enum_cls)
            return

        all_props = set()
        for prop in props:
            if prop not in self._prop_enum_cls:
                raise ParseQueryError(
                    f"Error: Given property to select: {prop.name} is not supported by query"
                )
            all_props.add(prop)

        self.selected_props = set(all_props)

    def generate_output(
        self, openstack_resources: List[OpenstackResourceObj]
    ) -> List[Dict[str, PropValue]]:
        """
        Generates a dictionary of queried properties from a list of openstack objects e.g. servers
        e.g. {['server_name': 'server1', 'server_id': 'server1_id'],
              ['server_name': 'server2', 'server_id': 'server2_id']} etc.
        (if we selected 'server_name' and 'server_id' as properties
        :param openstack_resources: List of openstack objects to obtain properties from - e.g. [Server1, Server2]
        :return: List containing dictionaries of the requested properties obtained from the items
        """
        output = []
        forwarded_outputs = deepcopy(self.forwarded_outputs)
        for item in openstack_resources:
            prop_list = self._parse_properties(item)
            prop_list.update(self._parse_forwarded_outputs(item, forwarded_outputs))
            output.append(prop_list)
        return output

    def _parse_forwarded_outputs(
        self, openstack_resource: OpenstackResourceObj, forwarded_outputs: Dict
    ) -> Dict[str, str]:
        """
        Generates a dictionary of forwarded outputs for the item given
        :param openstack_resource: openstack resource item to parse forwarded outputs for
        """
        forwarded_output_dict = {}
        for grouped_property, outputs in forwarded_outputs.items():
            prop_val = self._parse_property(grouped_property, openstack_resource)

            # this "should not" error because forwarded outputs should always be a super-set
            # but sometimes resolving the property fails for whatever reason - fail noisily
            try:
                output_list = outputs[prop_val]
                # we update with first result in grouped list and delete it

                # forwarded properties might contain more than one value
                # then() will keep duplicates so each one in the list will be shunted into an output
                forwarded_output_dict.update(output_list[0])

                # a hacky way to prevent one-to-many chaining erroring - keep at least one value
                # one-to-many/one-to-one will only ever contain one value per grouped_value
                # many-to-one will contain multiple values per grouped values
                if len(output_list) > 1:
                    del output_list[0]
            except KeyError as exp:
                raise QueryChainingError(
                    "Error: Chaining failed. Could not attach forwarded outputs.\n"
                    f"Property {grouped_property} extracted from has value {prop_val} which"
                    "does not match any values from forwarded outputs. "
                    "This is due to a mismatch in property mappings - likely an Openstack issue"
                ) from exp
        return forwarded_output_dict

    def _parse_properties(
        self, openstack_resource: OpenstackResourceObj
    ) -> Dict[str, PropValue]:
        """
        Generates a dictionary of queried properties from a single openstack object
        :param openstack_resource: openstack resource item to obtain properties from
        """
        obj_dict = {}
        for prop in self.selected_props:
            val = self._parse_property(prop, openstack_resource)
            obj_dict[prop.name.lower()] = val
        return obj_dict

    def _parse_property(
        self, prop: PropEnum, openstack_resource: OpenstackResourceObj
    ) -> PropValue:
        """
        Parse single property from an openstack_object and return result
        :param prop: property to parse
        :param openstack_resource: openstack resource item to obtain property from
        """
        prop_func = self._prop_enum_cls.get_prop_mapping(prop)
        try:
            val = str(prop_func(openstack_resource))
        except AttributeError:
            val = self.DEFAULT_OUT
        return val

    @staticmethod
    def _generate_table(
        results: List[Dict[str, PropValue]], return_html: bool, title=None, **kwargs
    ) -> str:
        """
        Returns a table from the result of 'self._parse_properties'
        :param results: dict of query results
        :param return_html: True if output required in html table format else output plain text table
        :param kwargs: kwargs to pass to tabulate
        :return: String (html or plaintext table of results)
        """
        output = ""
        if title:
            output += f"{title}\n"

        if results:
            headers = list(results[0].keys())
            rows = [list(row.values()) for row in results]
            output += tabulate(
                rows, headers, tablefmt="html" if return_html else "grid", **kwargs
            )
            output += "\n\n"
        else:
            output += "No results found"
        return output

    @staticmethod
    def flatten(data: Union[List, Dict]) -> Optional[Dict]:
        """
        Utility function for flattening output to instead get list of unique
        values found for each property selected. results will also be grouped if given
        data is grouped too
        :param data: output to flatten
        """
        if not data:
            return None

        if isinstance(data, list):
            return QueryOutput._flatten_list(data)

        result = {}
        for group_key, values in data.items():
            result[group_key] = QueryOutput._flatten_list(values)

        return result

    @staticmethod
    def _flatten_list(data: List[Dict]) -> Dict:
        """
        Helper function to flatten a query output list. This will return
        a dictionary where the keys are strings representing the property and
        the value is a list of unique values found in the given output list for that property.
        Output list can be actual query output (if it's a list) or one group of grouped results
        :param data: output list to flatten
        """
        if not data:
            return {}

        keys = list(data[0].keys())
        res = {}
        for key in keys:
            res[key] = [d[key] for d in data]
        return res
