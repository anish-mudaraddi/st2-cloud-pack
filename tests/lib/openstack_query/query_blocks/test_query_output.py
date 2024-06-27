from unittest.mock import MagicMock, patch, call, NonCallableMock, mock_open
import pytest

from exceptions.parse_query_error import ParseQueryError
from openstack_query.query_blocks.query_output import QueryOutput
from enums.query.props.server_properties import ServerProperties
from tests.lib.openstack_query.mocks.mocked_props import MockProperties


@pytest.fixture(name="instance")
def instance_fixture():
    """
    Returns an instance with mocked prop_enum_cls inject
    """
    mock_prop_enum_cls = MockProperties
    return QueryOutput(prop_enum_cls=mock_prop_enum_cls)


def test_selected_props(instance):
    """
    Tests that property method to get selected props works expectedly
    method should return self._props as a list
    """

    val = {
        MockProperties.PROP_1,
        MockProperties.PROP_2,
        MockProperties.PROP_3,
    }
    instance.selected_props = val
    assert instance.selected_props == list(val)


def test_selected_props_empty(instance):
    """
    Tests selected property method returns empty list when no props selected
    """
    assert instance.selected_props == []


def test_to_objects(instance):
    """
    Tests to_objects method with list results and no groups keyword given.
    Should call results_container.to_objects() and return as is
    """
    mock_results_container = MagicMock()
    mock_results_container.to_objects.return_value = NonCallableMock()
    res = instance.to_objects(mock_results_container)

    mock_results_container.to_objects.assert_called_once_with()
    assert res == mock_results_container.to_objects.return_value


def test_to_objects_ungrouped_results_with_group(instance):
    """
    Tests to_objects method with list results and groups keyword given.
    Should raise error
    """
    mock_results_container = MagicMock()
    mock_results_container.to_objects.return_value = [NonCallableMock()]
    with pytest.raises(ParseQueryError):
        instance.to_objects(mock_results_container, groups=["invalid-group"])


def test_to_objects_with_group_invalid(instance):
    """
    Tests to_objects method with dict results and groups keyword given.
    But groups provided contains invalid keys. Should raise error
    """
    mock_results_container = MagicMock()
    mock_results_container.to_objects.return_value = {"group1": [NonCallableMock()]}
    with pytest.raises(ParseQueryError):
        instance.to_objects(mock_results_container, groups=["invalid-group"])


def test_to_objects_with_group_valid(instance):
    """
    Tests to_objects method with dict results and groups keyword given.
    groups provided are valid keys. Should only return those keys
    """
    mock_results_container = MagicMock()
    groups = ["group1", "group2"]
    results_returned = {
        "group1": [NonCallableMock()],
        "group2": [NonCallableMock()],
        "group3": [NonCallableMock()],
    }
    expected = {k: results_returned[k] for k in groups}
    mock_results_container.to_objects.return_value = results_returned
    res = instance.to_objects(mock_results_container, groups=["group1", "group2"])
    mock_results_container.to_objects.assert_called_once_with()
    assert res == expected


def test_to_props(instance):
    """
    Tests to_props method with no extra params
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = NonCallableMock()
    res = instance.to_props(mock_results_container)
    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    assert res == mock_results_container.to_props.return_value


def test_to_props_ungrouped_results_with_flatten(instance):
    """
    Tests to_props method with list results and flatten given.
    Should run flatten
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = [
        {"prop1": "val1", "prop2": "val2"},
        {"prop1": "val3", "prop2": "val4"},
        {"prop1": "val5", "prop2": "val6"},
    ]
    res = instance.to_props(mock_results_container, flatten=True)
    assert res == {"prop1": ["val1", "val3", "val5"], "prop2": ["val2", "val4", "val6"]}


def test_to_props_grouped_results_with_flatten(instance):
    """
    Tests to_props method with dict results and flatten given.
    Should run flatten on each group
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [
            {"prop1": "val5", "prop2": "val6"},
            {"prop1": "val7", "prop2": "val8"},
        ],
    }

    res = instance.to_props(mock_results_container, flatten=True)
    assert res == {
        "group1": {"prop1": ["val1", "val3"], "prop2": ["val2", "val4"]},
        "group2": {"prop1": ["val5", "val7"], "prop2": ["val6", "val8"]},
    }


def test_to_props_results_empty_with_flatten(instance):
    """
    Tests to props method with empty list as results and flatten given
    should return None
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = []
    res = instance.to_props(mock_results_container, flatten=True)
    assert res is None


def test_to_props_grouped_results_with_flatten_and_group(instance):
    """
    Tests to_props method with dict results, with flatten and groups given.
    Should run flatten on each group
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [
            {"prop1": "val5", "prop2": "val6"},
            {"prop1": "val7", "prop2": "val8"},
        ],
    }

    res = instance.to_props(mock_results_container, groups=["group1"], flatten=True)
    assert res == {"group1": {"prop1": ["val1", "val3"], "prop2": ["val2", "val4"]}}


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_html_results_empty(mock_tabulate, instance):
    """
    Tests to_html method with no extra params and empty results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = []
    mock_tabulate.return_value = "tabulate-output"
    res = instance.to_html(mock_results_container)

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_not_called()
    assert res == "No results found<br/><br/>"


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_html_ungrouped_results(mock_tabulate, instance):
    """
    Tests to_html method with no extra params and ungrouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = [
        {"prop1": "val1", "prop2": "val2"},
        {"prop1": "val3", "prop2": "val4"},
    ]
    mock_tabulate.return_value = "tabulate-output"
    res = instance.to_html(mock_results_container)

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_called_once_with(
        [["val1", "val2"], ["val3", "val4"]], ["prop1", "prop2"], tablefmt="html"
    )

    assert res == "tabulate-output<br/><br/>"


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_html_grouped_results(mock_tabulate, instance):
    """
    Tests to_html method with no extra params and grouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [{"prop1": "val4", "prop2": "val5"}],
    }

    mock_tabulate.side_effect = ["tabulate-output-group1", "tabulate-output-group2"]

    res = instance.to_html(mock_results_container)

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_has_calls(
        [
            call(
                [["val1", "val2"], ["val3", "val4"]],
                ["prop1", "prop2"],
                tablefmt="html",
            ),
            call([["val4", "val5"]], ["prop1", "prop2"], tablefmt="html"),
        ]
    )

    assert res == (
        "<b>group1:</b><br/>tabulate-output-group1<br/><br/>"
        "<b>group2:</b><br/>tabulate-output-group2<br/><br/>"
    )


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_html_with_title(mock_tabulate, instance):
    """
    Tests to_html method with title param and ungrouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = [
        {"prop1": "val1", "prop2": "val2"},
        {"prop1": "val3", "prop2": "val4"},
    ]
    mock_tabulate.return_value = "tabulate-output"
    res = instance.to_html(mock_results_container, title="mock-title")

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_called_once_with(
        [["val1", "val2"], ["val3", "val4"]], ["prop1", "prop2"], tablefmt="html"
    )

    assert res == ("<b>mock-title:</b><br/>" "tabulate-output<br/><br/>")


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_html_with_title_grouped_results(mock_tabulate, instance):
    """
    Tests to_html method with title param and grouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [{"prop1": "val4", "prop2": "val5"}],
    }

    mock_tabulate.side_effect = ["tabulate-output-group1", "tabulate-output-group2"]

    res = instance.to_html(mock_results_container, title="mock-title")

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_has_calls(
        [
            call(
                [["val1", "val2"], ["val3", "val4"]],
                ["prop1", "prop2"],
                tablefmt="html",
            ),
            call([["val4", "val5"]], ["prop1", "prop2"], tablefmt="html"),
        ]
    )

    assert res == (
        "<b>mock-title:</b><br/>"
        "<b>group1:</b><br/>tabulate-output-group1<br/><br/>"
        "<b>group2:</b><br/>tabulate-output-group2<br/><br/>"
    )


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_html_with_title_and_group(mock_tabulate, instance):
    """
    Tests to_html method with title and group params and grouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [{"prop1": "val4", "prop2": "val5"}],
    }

    mock_tabulate.side_effect = ["tabulate-output-group2"]

    res = instance.to_html(
        mock_results_container, title="mock-title", groups=["group2"]
    )

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_called_once_with(
        [["val4", "val5"]], ["prop1", "prop2"], tablefmt="html"
    )

    assert res == (
        "<b>mock-title:</b><br/>" "<b>group2:</b><br/>tabulate-output-group2<br/><br/>"
    )


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_string_results_empty(mock_tabulate, instance):
    """
    Tests to_string method with no extra params and empty results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = []
    mock_tabulate.return_value = "tabulate-output"
    res = instance.to_string(mock_results_container)

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_not_called()
    assert res == "No results found\n\n"


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_string_ungrouped_results(mock_tabulate, instance):
    """
    Tests to_string method with no extra params and ungrouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = [
        {"prop1": "val1", "prop2": "val2"},
        {"prop1": "val3", "prop2": "val4"},
    ]
    mock_tabulate.return_value = "tabulate-output"
    res = instance.to_string(mock_results_container)

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_called_once_with(
        [["val1", "val2"], ["val3", "val4"]], ["prop1", "prop2"], tablefmt="grid"
    )

    assert res == "tabulate-output\n\n"


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_string_grouped_results(mock_tabulate, instance):
    """
    Tests to_string method with no extra params and grouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [{"prop1": "val4", "prop2": "val5"}],
    }

    mock_tabulate.side_effect = ["tabulate-output-group1", "tabulate-output-group2"]

    res = instance.to_string(mock_results_container)

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_has_calls(
        [
            call(
                [["val1", "val2"], ["val3", "val4"]],
                ["prop1", "prop2"],
                tablefmt="grid",
            ),
            call([["val4", "val5"]], ["prop1", "prop2"], tablefmt="grid"),
        ]
    )

    assert res == (
        "group1:\ntabulate-output-group1\n\n" "group2:\ntabulate-output-group2\n\n"
    )


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_string_with_title(mock_tabulate, instance):
    """
    Tests to_string method with title param and ungrouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = [
        {"prop1": "val1", "prop2": "val2"},
        {"prop1": "val3", "prop2": "val4"},
    ]
    mock_tabulate.return_value = "tabulate-output"
    res = instance.to_string(mock_results_container, title="mock-title")

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_called_once_with(
        [["val1", "val2"], ["val3", "val4"]], ["prop1", "prop2"], tablefmt="grid"
    )

    assert res == ("mock-title:\n" "tabulate-output\n\n")


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_string_with_title_grouped_results(mock_tabulate, instance):
    """
    Tests to_string method with title param and grouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [{"prop1": "val4", "prop2": "val5"}],
    }

    mock_tabulate.side_effect = ["tabulate-output-group1", "tabulate-output-group2"]

    res = instance.to_string(mock_results_container, title="mock-title")

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_has_calls(
        [
            call(
                [["val1", "val2"], ["val3", "val4"]],
                ["prop1", "prop2"],
                tablefmt="grid",
            ),
            call([["val4", "val5"]], ["prop1", "prop2"], tablefmt="grid"),
        ]
    )

    assert res == (
        "mock-title:\n"
        "group1:\ntabulate-output-group1\n\n"
        "group2:\ntabulate-output-group2\n\n"
    )


@patch("openstack_query.query_blocks.query_output.tabulate")
def test_to_string_with_title_and_group(mock_tabulate, instance):
    """
    Tests to_string method with title and group params and grouped results
    """
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [{"prop1": "val4", "prop2": "val5"}],
    }

    mock_tabulate.side_effect = ["tabulate-output-group2"]

    res = instance.to_string(
        mock_results_container, title="mock-title", groups=["group2"]
    )

    mock_results_container.to_props.assert_called_once_with(*instance.selected_props)
    mock_tabulate.assert_called_once_with(
        [["val4", "val5"]], ["prop1", "prop2"], tablefmt="grid"
    )

    assert res == ("mock-title:\n" "group2:\ntabulate-output-group2\n\n")


def test_parse_select_with_select_all(instance):
    """
    tests that parse select works expectedly - when called from select_all() - no props given
    method should set props internal attribute to all available props supported by prop_handler
    """
    # if select_all flag set, get all props
    instance.parse_select(select_all=True)
    assert instance.selected_props == list(set(MockProperties))


def test_parse_select_given_args(instance):
    """
    tests that parse select works expectedly - when called from select() - where props args given
    method should set check each given prop to see if mapping exists in prop_handler and
    add to internal attribute set props
    """
    # if given props
    instance.parse_select(MockProperties.PROP_1, MockProperties.PROP_2)
    assert instance.selected_props, [MockProperties.PROP_1, MockProperties.PROP_2]


def test_parse_select_given_invalid(instance):
    """
    Tests that parse_select works expectedly
    method should raise error when given an invalid prop enum
    """

    # server prop enums are invalid here and should be picked up
    with pytest.raises(ParseQueryError):
        instance.parse_select([MockProperties.PROP_1, ServerProperties.SERVER_ID])


def test_parse_select_overwrites_old(instance):
    """
    Tests that parse_select overwrites old selected_props
    method should overwrite internal attribute selected_props if already set
    """
    instance.selected_props = [MockProperties.PROP_1]
    instance.parse_select([MockProperties.PROP_2])
    assert instance.selected_props == [MockProperties.PROP_2]


@patch("builtins.open", new_callable=mock_open)
@patch("openstack_query.query_blocks.query_output.csv.DictWriter")
@patch("openstack_query.query_blocks.query_output.Path")
def test_to_csv_ungrouped_results(
    mock_path, mock_dict_writer, mock_open_call, instance
):
    """
    Tests to_csv with ungrouped results - should call open to write a single file
    """
    mock_dir_path = NonCallableMock()
    mock_file_path = mock_path.return_value.joinpath.return_value
    mock_results = [
        {"prop1": "val1", "prop2": "val2"},
        {"prop1": "val3", "prop2": "val4"},
    ]

    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = mock_results

    instance.to_csv(mock_results_container, mock_dir_path)
    mock_path.assert_has_calls(
        [
            call(mock_dir_path),
            call().joinpath("query_out.csv"),
        ]
    )
    assert mock_open_call.call_args_list == [
        call(mock_file_path, "w", encoding="utf-8")
    ]
    mock_dict_writer.assert_has_calls(
        [
            call(
                mock_open_call.return_value,
                fieldnames=mock_results[0].keys(),
            ),
            call().writeheader(),
            call().writerows(mock_results),
        ]
    )


@patch("builtins.open", new_callable=mock_open)
@patch("openstack_query.query_blocks.query_output.csv.DictWriter")
@patch("openstack_query.query_blocks.query_output.Path")
def test_to_csv_grouped_results(mock_path, mock_dict_writer, mock_open_call, instance):
    """
    Tests to_csv with grouped results - should call open to write multiple files
    one for each group in results
    """
    mock_dir_path = NonCallableMock()
    mock_file_path = mock_path.return_value.joinpath.return_value
    mock_results = {
        "group1": [
            {"prop1": "val1", "prop2": "val2"},
            {"prop1": "val3", "prop2": "val4"},
        ],
        "group2": [
            {"prop1": "val5", "prop2": "val6"},
            {"prop1": "val7", "prop2": "val8"},
        ],
    }

    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = mock_results

    instance.to_csv(mock_results_container, mock_dir_path)

    mock_path.assert_has_calls(
        [
            call(mock_dir_path),
            call().joinpath("group1.csv"),
            call().joinpath("group2.csv"),
        ]
    )

    assert mock_open_call.call_args_list == [
        call(mock_file_path, "w", encoding="utf-8"),
        call(mock_file_path, "w", encoding="utf-8"),
    ]

    mock_dict_writer.assert_has_calls(
        [
            call(
                mock_open_call.return_value,
                fieldnames=mock_results["group1"][0].keys(),
            ),
            call().writeheader(),
            call().writerows(mock_results["group1"]),
            call(
                mock_open_call.return_value,
                fieldnames=mock_results["group2"][0].keys(),
            ),
            call().writeheader(),
            call().writerows(mock_results["group2"]),
        ]
    )


@patch("openstack_query.query_blocks.query_output.Path")
def test_to_csv_results_empty(mock_path, instance):
    """
    Tests to_csv with empty results - should raise Runtime error
    """
    mock_dir_path = NonCallableMock()
    mock_results_container = MagicMock()
    mock_results_container.to_props.return_value = []

    with pytest.raises(RuntimeError):
        instance.to_csv(mock_results_container, mock_dir_path)
    assert mock_path.call_args_list == [call(mock_dir_path)]
    assert mock_path.return_value.joinpath.call_args_list == [call("query_out.csv")]
