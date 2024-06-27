import csv
from typing import List, Dict, Union, Type, Set, Optional
from pathlib import Path
from tabulate import tabulate
from enums.query.props.prop_enum import PropEnum
from custom_types.openstack_query.aliases import PropValue
from exceptions.parse_query_error import ParseQueryError
from openstack_query.query_blocks.results_container import ResultsContainer


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

    @staticmethod
    def _validate_groups(
        results: Union[List, Dict], groups: Optional[List[str]] = None
    ):
        """
        helper method which takes a set of grouped results and a list of groups and
        outputs a subset of results where each key in subset matches a value in given set of groups.
        method will return all results if groups not given.
        Outputs error if:
            - groups contains a value not in results
            - given results aren't grouped
        :param results: results to get subset for if grouped and groups given
        :param groups: an optional list of keys to get a subset of results
        """
        if not groups:
            return results

        if not isinstance(results, dict):
            raise ParseQueryError(
                f"Result is not grouped - cannot filter by given group(s) {groups}"
            )
        if not all(group in results.keys() for group in groups):
            raise ParseQueryError(
                f"Group(s) given are invalid - valid groups {list(results.keys())}"
            )
        return {group_key: results[group_key] for group_key in groups}

    def to_objects(
        self, results_container: ResultsContainer, groups: Optional[List[str]] = None
    ) -> Union[Dict[str, List], List]:
        """
        return results as openstack objects
        :param results_container: container object which stores results
        :param groups: a list of group keys to limit output by

        """
        results = results_container.to_objects()
        return self._validate_groups(results, groups)

    def to_props(
        self,
        results_container: ResultsContainer,
        flatten: bool = False,
        groups: Optional[List[str]] = None,
    ) -> Union[Dict[str, List], List]:
        """
        return results as selected props
        :param results_container: container object which stores results
        :param flatten: boolean which will flatten results if true
        :param groups: a list of group keys to limit output by
        """
        results = results_container.to_props(*self.selected_props)
        results = self._validate_groups(results, groups)
        if flatten:
            results = self._flatten(results)
        return results

    def to_string(
        self,
        results_container: ResultsContainer,
        title: str = None,
        groups: Optional[List[str]] = None,
        include_group_titles: [bool] = True,
        **kwargs,
    ):
        """
        return results as a table of selected properties
        :param results_container: container object which stores results
        :param title: an optional title for the table when it gets outputted
        :param groups: a list of groups to limit output by
        :param include_group_titles: include group name as subtitle when printing groups
        :param kwargs: kwargs to pass to _generate_table method
        """
        results = results_container.to_props(*self.selected_props)
        results = self._validate_groups(results, groups)

        output = "" if not title else f"{title}:\n"

        if isinstance(results, dict):
            for group_title in list(results.keys()):
                output += self._generate_table(
                    results[group_title],
                    return_html=False,
                    title=f"{group_title}:\n" if include_group_titles else None,
                    **kwargs,
                )
                output += "\n\n"
        else:
            output += self._generate_table(
                results, return_html=False, title=None, **kwargs
            )
            output += "\n\n"
        return output

    def to_html(
        self,
        results_container: ResultsContainer,
        title: str = None,
        groups: Optional[List[str]] = None,
        include_group_titles: bool = True,
        **kwargs,
    ) -> str:
        """
        method to return results as html table
        :param results_container: container object which stores results
        :param title: a title for the table(s) when it gets outputted
        :param groups: a list of groups to limit output by
        :param include_group_titles: include group name as subtitle when printing groups
        :param kwargs: kwargs to pass to generate table
        """
        results = results_container.to_props(*self.selected_props)
        results = self._validate_groups(results, groups)
        output = "" if not title else f"<b>{title}:</b><br/>"

        if isinstance(results, dict):
            for group_title in list(results.keys()):
                output += self._generate_table(
                    results[group_title],
                    return_html=True,
                    title=(
                        f"<b>{group_title}:</b><br/>" if include_group_titles else None
                    ),
                    **kwargs,
                )
                output += "<br/><br/>"
        else:
            output += self._generate_table(
                results, return_html=True, title=None, **kwargs
            )
            output += "<br/><br/>"
        return output

    def _parse_select_inputs(self, props):
        """
        Converts list of select() 'prop' user inputs into Enums, any string aliases will be converted into Enums
        :param props: one or more Enums/string aliases representing properties to show
        """
        parsed_props = []
        for prop in props:
            if isinstance(prop, str):
                prop = self._prop_enum_cls.from_string(prop)
            parsed_props.append(prop)
        return parsed_props

    def parse_select(
        self, props: Optional[List[Union[str, PropEnum]]] = None, select_all=False
    ) -> None:
        """
        Method which is used to set which properties to output once results are gathered
        This method checks that each Enum provided is valid and populates internal attribute which holds selected props
        :param props: one or more Enums/string aliases representing properties to show
        :param select_all: boolean flag to select all valid properties
        """

        if select_all:
            self.selected_props = set(self._prop_enum_cls)
            return

        props = self._parse_select_inputs(props)
        all_props = set()
        for prop in props:
            if prop not in self._prop_enum_cls:
                raise ParseQueryError(
                    f"Error: Given property to select: {prop.name} is not supported by query"
                )
            all_props.add(prop)

        self.selected_props = set(all_props)

    @staticmethod
    def _generate_table(
        results: List[Dict[str, PropValue]], return_html: bool, title=None, **kwargs
    ) -> str:
        """
        Returns a table from the result of 'self.parse_properties'
        :param results: dict of query results
        :param return_html: True if output required in html table format else output plain text table
        :param kwargs: kwargs to pass to tabulate
        :return: String (html or plaintext table of results)
        """
        output = "" if not title else f"{title}"

        if results:
            headers = list(results[0].keys())
            rows = [list(row.values()) for row in results]
            output += tabulate(
                rows, headers, tablefmt="html" if return_html else "grid", **kwargs
            )
        else:
            output += "No results found"
        return output

    @staticmethod
    def _flatten(data: Union[List, Dict]) -> Optional[Dict]:
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

    @staticmethod
    def _write_file(data: Union[List, Dict], output_filepath: Path) -> None:
        """
        takes a list of results, calls to_props() and outputs them to a file
        :param data: list of results to write
        :param output_filepath: Path object containing filepath to write to
        """

        if not data or not data[0].keys():
            raise RuntimeError(
                "Error: Could not write to csv file: "
                "No results found, or no properties selected to output"
            )

        fields = data[0].keys()
        with open(output_filepath, "w", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def _write_files(data: Union[List, Dict], dir_path: Path) -> None:
        """
        takes grouped results and outputs each group to a separate file in specified directory
        :param data: grouped results to write to files
        :param dir_path: Path object containing path to directory the files will be written to
        """
        for group_name_id, group_item_info in data.items():
            file_path = dir_path.joinpath(f"{group_name_id}.csv")
            QueryOutput._write_file(group_item_info, file_path)

    def to_csv(self, results_container: ResultsContainer, dir_path: str) -> None:
        """
        Method to return results as csv files. Will output grouped results as separate files.
        :param results_container: container object which stores results
        :param dir_path: string representing a directory path where csv files will be created in.
            - If results aren't grouped, file called "query_out.csv" will be written inside the directory
            - If results are grouped, files matching the group keys will be written inside the directory
        """
        dir_path = Path(dir_path)
        data = self.to_props(results_container)

        if isinstance(data, list):
            filepath = dir_path.joinpath("query_out.csv")
            return self._write_file(data, filepath)
        return self._write_files(data, dir_path)
