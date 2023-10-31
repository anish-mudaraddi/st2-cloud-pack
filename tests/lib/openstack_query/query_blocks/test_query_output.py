from unittest.mock import MagicMock, patch, call, NonCallableMock
import pytest

from exceptions.query_chaining_error import QueryChainingError
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


@patch("openstack_query.query_blocks.query_output.QueryOutput._generate_table")
def test_to_html_with_list_results(mock_generate_table, instance):
    """
    Tests that to_html function works expectedly - when given list as results and no title
    method should call generate_table with return_html once
    """

    mocked_results = ["obj1", "obj2"]
    mock_generate_table.return_value = "mock out"
    res = instance.to_html(results=mocked_results, title="mock title")
    mock_generate_table.assert_called_once_with(
        mocked_results, return_html=True, title=None
    )
    assert res == "<b> mock title </b><br/> mock out"


@patch("openstack_query.query_blocks.query_output.QueryOutput._generate_table")
def test_to_html_with_no_title(mock_generate_table, instance):
    """
    Tests that to_html function works expectedly - when given list as results and no title
    method should call generate_table with return_html once
    """

    mocked_results = ["obj1", "obj2"]
    mock_generate_table.return_value = "mock out"
    res = instance.to_html(results=mocked_results, title=None)
    mock_generate_table.assert_called_once_with(
        mocked_results, return_html=True, title=None
    )
    assert res == "mock out"


@patch("openstack_query.query_blocks.query_output.QueryOutput._generate_table")
def test_to_html_with_grouped_results(mock_generate_table, instance):
    """
    Tests that to_html function works expectedly - when given grouped results
    method should call generate_table with return_html for each group
    """
    mocked_results = {"group1": ["obj1", "obj2"], "group2": ["obj3", "obj4"]}

    mock_generate_table.side_effect = ["1 out, ", "2 out"]
    res = instance.to_html(results=mocked_results, title="mock title")

    mock_generate_table.assert_has_calls(
        [
            call(["obj1", "obj2"], return_html=True, title="<b> group1: </b><br/> "),
            call(["obj3", "obj4"], return_html=True, title="<b> group2: </b><br/> "),
        ]
    )
    assert res == "<b> mock title </b><br/> 1 out, 2 out"


def test_to_html_incorrect_groups(instance):
    """
    Tests that to_html function raises error when given a group that doesn't appear in results
    """
    mocked_results = {"group1": ["obj1", "obj2"], "group2": ["obj3", "obj4"]}
    with pytest.raises(ParseQueryError):
        instance.to_html(results=mocked_results, groups=["group3"])


def test_to_html_errors_when_not_grouped(instance):
    """
    Tests that to_html function raises error when given a group and results are not grouped
    """
    mocked_results = ["obj1", "obj2"]
    with pytest.raises(ParseQueryError):
        instance.to_html(results=mocked_results, groups=["group3"])


@patch("openstack_query.query_blocks.query_output.QueryOutput._generate_table")
def test_to_string_with_list_results(mock_generate_table, instance):
    """
    Tests that to_string function works expectedly - when given list as results
    method should call generate_table with return_html set to false once
    """

    mocked_results = ["obj1", "obj2"]
    mock_generate_table.return_value = "mock out"

    res = instance.to_string(results=mocked_results, title="mock title")
    mock_generate_table.assert_called_once_with(
        mocked_results, return_html=False, title=None
    )
    assert "mock title:\nmock out" == res


@patch("openstack_query.query_blocks.query_output.QueryOutput._generate_table")
def test_to_string_with_no_title(mock_generate_table, instance):
    """
    Tests that to_string function works expectedly - when given list as results and no title
    method should call generate_table with return_html set to false once
    """

    mocked_results = ["obj1", "obj2"]
    mock_generate_table.return_value = "mock out"

    res = instance.to_string(results=mocked_results, title=None)
    mock_generate_table.assert_called_once_with(
        mocked_results, return_html=False, title=None
    )
    assert "mock out" == res


@patch("openstack_query.query_blocks.query_output.QueryOutput._generate_table")
def test_to_string_with_grouped_results(mock_generate_table, instance):
    """
    Tests that to_string function works expectedly - when given grouped results
    method should call generate_table with return_html set to false for each group
    """
    mocked_results = {"group1": ["obj1", "obj2"], "group2": ["obj3", "obj4"]}
    mock_generate_table.side_effect = ["1 out, ", "2 out"]

    res = instance.to_string(results=mocked_results, title="mock title")

    mock_generate_table.assert_has_calls(
        [
            call(["obj1", "obj2"], return_html=False, title="group1:\n"),
            call(["obj3", "obj4"], return_html=False, title="group2:\n"),
        ]
    )
    assert "mock title:\n1 out, 2 out" == res


def test_to_string_incorrect_groups(instance):
    """
    Tests that to_html function raises error when given a group that doesn't appear in results
    """
    mocked_results = {"group1": ["obj1", "obj2"], "group2": ["obj3", "obj4"]}
    with pytest.raises(ParseQueryError):
        instance.to_string(results=mocked_results, groups=["group3"])


def test_to_string_errors_when_not_grouped(instance):
    """
    Tests that to_string function raises error when given a group and results are not grouped
    """
    mocked_results = ["obj1", "obj2"]
    with pytest.raises(ParseQueryError):
        instance.to_string(results=mocked_results, groups=["group3"])


def test_generate_table_no_vals(instance):
    """
    Tests that generate_table function works expectedly - when results empty
    method should return No results found
    """
    results_dict_0 = []

    # pylint:disable=protected-access
    res = instance._generate_table(
        results_dict_0, title="mock title", return_html=False
    )
    assert "mock title\nNo results found" == res


@pytest.mark.parametrize(
    "return_html, expected_tablefmt", [(True, "html"), (False, "grid")]
)
@patch("openstack_query.query_blocks.query_output.tabulate")
def test_generate_table_single_row_single_col(
    mock_tabulate, return_html, expected_tablefmt, instance
):
    """
    Tests that generate_table function works expectedly - with single result, single selected prop
    method should format results dict and call tabulate and return a string of the tabled results
    """
    mock_results = [{"prop1": "val1"}]
    mock_tabulate.return_value = "mock out"

    # pylint:disable=protected-access
    res = instance._generate_table(mock_results, return_html=return_html, title=None)
    mock_tabulate.assert_called_once_with(
        [["val1"]], ["prop1"], tablefmt=expected_tablefmt
    )
    assert res == "mock out\n\n"


@pytest.mark.parametrize(
    "return_html, expected_tablefmt", [(True, "html"), (False, "grid")]
)
@patch("openstack_query.query_blocks.query_output.tabulate")
def test_generate_table_multi_row_single_col(
    mock_tabulate, return_html, expected_tablefmt, instance
):
    """
    Tests that generate_table function works expectedly - with multiple results, single selected prop
    method should format results dict and call tabulate and return a string of the tabled results
    """
    mock_results = [{"prop1": "val1"}, {"prop1": "val2"}]
    mock_tabulate.return_value = "mock out"

    # pylint:disable=protected-access
    res = instance._generate_table(mock_results, return_html=return_html, title=None)
    mock_tabulate.assert_called_once_with(
        [["val1"], ["val2"]], ["prop1"], tablefmt=expected_tablefmt
    )
    assert res == "mock out\n\n"


@pytest.mark.parametrize(
    "return_html, expected_tablefmt", [(True, "html"), (False, "grid")]
)
@patch("openstack_query.query_blocks.query_output.tabulate")
def test_generate_table_single_row_multi_col(
    mock_tabulate, return_html, expected_tablefmt, instance
):
    """
    Tests that generate_table function works expectedly - with single result, multiple selected prop
    method should format results dict and call tabulate and return a string of the tabled results
    """
    mock_results = [{"prop1": "val1", "prop2": "val2"}]
    mock_tabulate.return_value = "mock out"

    # pylint:disable=protected-access
    res = instance._generate_table(mock_results, return_html=return_html, title=None)
    mock_tabulate.assert_called_once_with(
        [["val1", "val2"]], ["prop1", "prop2"], tablefmt=expected_tablefmt
    )
    assert res == "mock out\n\n"


@pytest.mark.parametrize(
    "return_html, expected_tablefmt", [(True, "html"), (False, "grid")]
)
@patch("openstack_query.query_blocks.query_output.tabulate")
def test_generate_table_multi_row_multi_col(
    mock_tabulate, return_html, expected_tablefmt, instance
):
    """
    Tests that generate_table function works expectedly - with multiple results, multiple selected prop
    method should format results dict and call tabulate and return a string of the tabled results
    """
    mock_results = [
        {"prop1": "val1", "prop2": "val2"},
        {"prop1": "val3", "prop2": "val4"},
    ]
    mock_tabulate.return_value = "mock out"

    # pylint:disable=protected-access
    res = instance._generate_table(mock_results, return_html=return_html, title=None)
    mock_tabulate.assert_called_once_with(
        [["val1", "val2"], ["val3", "val4"]],
        ["prop1", "prop2"],
        tablefmt=expected_tablefmt,
    )
    assert res == "mock out\n\n"


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
        instance.parse_select(MockProperties.PROP_1, ServerProperties.SERVER_ID)


def test_parse_select_overwrites_old(instance):
    """
    Tests that parse_select overwrites old selected_props
    method should overwrite internal attribute selected_props if already set
    """
    instance.selected_props = [MockProperties.PROP_1]
    instance.parse_select(MockProperties.PROP_2)
    assert instance.selected_props == [MockProperties.PROP_2]


def test_generate_output_no_items(instance):
    """
    Tests that generate_output method works expectedly - no openstack items
    method should return an empty list
    """
    assert instance.generate_output([]) == []


@patch("openstack_query.query_blocks.query_output.QueryOutput._parse_properties")
@patch("openstack_query.query_blocks.query_output.QueryOutput._parse_forwarded_outputs")
@patch("openstack_query.query_blocks.query_output.deepcopy")
def test_generate_output_one_item(
    mock_deepcopy, mock_parse_forwarded_outputs, mock_parse_properties, instance
):
    """
    Tests generate output method - with a list containing one item
    """
    instance.update_forwarded_outputs(NonCallableMock(), NonCallableMock())
    mock_parse_properties.return_value = {"prop1": "val1", "prop2": "val2"}
    mock_parse_forwarded_outputs.return_value = {
        "output_prop3": "val3",
        "output_prop4": "val4",
    }

    res = instance.generate_output(["obj1"])
    mock_deepcopy.assert_called_once_with(instance.forwarded_outputs)
    mock_parse_properties.assert_called_once_with("obj1")
    mock_parse_forwarded_outputs.assert_called_once_with(
        "obj1", mock_deepcopy.return_value
    )
    assert res == [
        {
            "prop1": "val1",
            "prop2": "val2",
            "output_prop3": "val3",
            "output_prop4": "val4",
        }
    ]


@patch("openstack_query.query_blocks.query_output.QueryOutput._parse_properties")
@patch("openstack_query.query_blocks.query_output.QueryOutput._parse_forwarded_outputs")
@patch("openstack_query.query_blocks.query_output.deepcopy")
def test_generate_output_many_items(
    mock_deepcopy, mock_parse_forwarded_outputs, mock_parse_properties, instance
):
    """
    Tests generate output method - with a list containing one item
    """
    instance.update_forwarded_outputs(NonCallableMock(), NonCallableMock())

    mock_parse_properties.side_effect = [
        {"prop1": "val1", "prop2": "val2"},
        {"prop1": "val3", "prop2": "val4"},
    ]
    mock_parse_forwarded_outputs.side_effect = [
        {"output_prop1": "val1", "output_prop2": "val2"},
        {"output_prop1": "val3", "output_prop2": "val4"},
    ]

    res = instance.generate_output(["obj1", "obj2"])
    mock_deepcopy.assert_called_once_with(instance.forwarded_outputs)

    mock_parse_properties.assert_has_calls([call("obj1"), call("obj2")])
    mock_parse_forwarded_outputs.asssert_has_calls(
        [
            call("obj1", mock_deepcopy.return_value),
            call("obj2", mock_deepcopy.return_value),
        ]
    )

    expected_vals = [
        {
            "prop1": "val1",
            "prop2": "val2",
            "output_prop1": "val1",
            "output_prop2": "val2",
        },
        {
            "prop1": "val3",
            "prop2": "val4",
            "output_prop1": "val3",
            "output_prop2": "val4",
        },
    ]
    assert res == expected_vals


@pytest.fixture(name="mock_get_prop_func")
def get_prop_func_fixture():
    """
    Stubs out get_prop_func method to return a
    stub callable based on prop enum
    """
    mock_prop_1_func = MagicMock()
    mock_prop_1_func.return_value = "prop 1 out"

    mock_prop_2_func = MagicMock()
    mock_prop_2_func.side_effect = AttributeError

    def _mock_get_prop_func(prop):
        return {
            MockProperties.PROP_1: mock_prop_1_func,
            MockProperties.PROP_2: mock_prop_2_func,
        }.get(prop, None)

    return _mock_get_prop_func


def test_parse_properties_no_props(instance):
    """
    Tests that parse_properties function works expectedly with 0 prop_funcs to apply
    method should return an empty dict
    """

    # mock get_prop_mapping to return a func string appropriate for that prop
    instance.selected_props = set()
    # pylint:disable=protected-access
    assert instance._parse_properties("openstack-item") == {}


@patch.object(MockProperties, "get_prop_mapping")
def test_parse_properties_one_prop(mock_get_prop_func, instance):
    """
    Tests that parse_properties function works expectedly with 0 prop_funcs to apply
    method should return a dict with one key value pair (prop-name, prop-value)
    """
    mock_prop_func = MagicMock()
    mock_prop_func.return_value = "prop 1 out"

    mock_get_prop_func.return_value = mock_prop_func

    instance.selected_props = {MockProperties.PROP_1}
    # pylint:disable=protected-access
    res = instance._parse_properties("openstack-item")

    mock_get_prop_func.assert_called_once_with(MockProperties.PROP_1)
    mock_prop_func.assert_called_once_with("openstack-item")

    assert res == {"prop_1": "prop 1 out"}


def test_parse_properties_many_props(mock_get_prop_func, instance):
    """
    Tests that parse_properties function works expectedly with 0 prop_funcs to apply
    method should return a dict with many key value pairs (prop-name, prop-value)
    """

    instance.selected_props = {MockProperties.PROP_1, MockProperties.PROP_2}

    with patch.object(
        MockProperties, "get_prop_mapping", wraps=mock_get_prop_func
    ) as mock_get_prop_mapping:
        # pylint:disable=protected-access
        res = instance._parse_properties("openstack-item")

    assert res == {"prop_1": "prop 1 out", "prop_2": "Not Found"}
    mock_get_prop_mapping.assert_has_calls(
        [call(prop) for prop in instance.selected_props]
    )


def test_flatten_empty(instance):
    """
    Tests that flatten() function works expectedly - with empty list/dict
    """
    assert instance.flatten([]) is None
    assert instance.flatten({}) is None


def test_flatten_with_list(instance):
    """
    Tests that flatten() functions works expectedly - with a non-empty list
    should call flatten_list
    """
    with patch(
        "openstack_query.query_blocks.query_output.QueryOutput._flatten_list"
    ) as mock_flatten_list:
        res = instance.flatten(["obj1", "obj2"])
    mock_flatten_list.assert_called_once_with(["obj1", "obj2"])
    assert res == mock_flatten_list.return_value


def test_flatten_with_dict_one_group(instance):
    """
    Tests that flatten() functions works expectedly
    with a non-empty results with one group - should call flatten list once
    """
    with patch(
        "openstack_query.query_blocks.query_output.QueryOutput._flatten_list"
    ) as mock_flatten_list:
        res = instance.flatten({"group1": ["obj1", "obj2"]})
    mock_flatten_list.assert_called_once_with(["obj1", "obj2"])
    assert res == {"group1": mock_flatten_list.return_value}


def test_flatten_with_dict_many_groups(instance):
    """
    Tests that flatten() functions works expectedly
    with a non-empty result with many groups - should call flatten list with each group
    """
    with patch(
        "openstack_query.query_blocks.query_output.QueryOutput._flatten_list"
    ) as mock_flatten_list:
        res = instance.flatten({"group1": ["obj1", "obj2"], "group2": ["obj3", "obj4"]})
    mock_flatten_list.assert_has_calls([call(["obj1", "obj2"]), call(["obj3", "obj4"])])
    assert res == {
        "group1": mock_flatten_list.return_value,
        "group2": mock_flatten_list.return_value,
    }


def test_flatten_list_empty_list(instance):
    """
    Tests that flatten_list() function works expectedly
    with an empty list - should return an empty dictionary
    """
    # pylint:disable=protected-access
    assert instance._flatten_list([]) == {}


def test_flatten_list_one_key_one_item(instance):
    """
    Tests flatten_list() function with one item with one key-value pair
    """
    # pylint:disable=protected-access
    assert instance._flatten_list([{"prop1": "val1"}]) == {"prop1": ["val1"]}


def test_flatten_list_many_keys_one_item(instance):
    """
    Tests flatten_list() function with one item with many key-value pairs
    """
    # pylint:disable=protected-access
    assert instance._flatten_list([{"prop1": "val1", "prop2": "val2"}]) == {
        "prop1": ["val1"],
        "prop2": ["val2"],
    }


def test_flatten_list_many_keys_many_items(instance):
    """
    Tests flatten_list() function with many items with many key-value pairs
    """
    # pylint:disable=protected-access
    assert instance._flatten_list(
        [{"prop1": "val1", "prop2": "val2"}, {"prop1": "val3", "prop2": "val4"}]
    ) == {"prop1": ["val1", "val3"], "prop2": ["val2", "val4"]}


def test_flatten_with_duplicates(instance):
    """
    Tests flatten_list() function with duplicates - should keep duplicates as is
    """
    # pylint:disable=protected-access
    assert instance._flatten_list(
        [{"prop1": "val1", "prop2": "val2"}, {"prop1": "val1", "prop2": "val2"}]
    ) == {"prop1": ["val1", "val1"], "prop2": ["val2", "val2"]}


def test_update_forwarded_outputs(instance):
    """
    Tests update_forwarded_outputs() method
    ensure various test cases when running update_forwarded_outputs succeeds
    """

    # test update with one output set when forwarded_outputs empty
    instance.update_forwarded_outputs("prop1", "output")
    assert instance.forwarded_outputs == {"prop1": "output"}

    # test add another another output set - different group key
    instance.update_forwarded_outputs("prop2", "output2")
    assert instance.forwarded_outputs == {"prop1": "output", "prop2": "output2"}

    # test update works - same group key
    instance.update_forwarded_outputs("prop1", "output-new")
    assert instance.forwarded_outputs == {"prop1": "output-new", "prop2": "output2"}


def test_parse_forwarded_outputs_no_set(instance):
    """
    Tests parse_forwarded_outputs() method - with no forwarded_outputs set
    should return empty dict
    """
    # pylint:disable=protected-access
    assert instance._parse_forwarded_outputs("obj1", {}) == {}


@patch("openstack_query.query_blocks.query_output.QueryOutput._parse_property")
def test_parse_forwarded_outputs_one_to_many(mock_parse_property, instance):
    """
    Tests parse_forwarded_outputs() method - one set of forwarded_outputs
    """
    expected_out = {"forwarded-prop1": "val1", "forwarded-prop2": "val2"}
    mock_forwarded_outputs = {"prop1": {"prop_val1": [expected_out]}}

    mock_parse_property.side_effect = ["prop_val1", "prop_val1"]

    # pylint:disable=protected-access

    # first match
    res = instance._parse_forwarded_outputs("obj1", mock_forwarded_outputs)
    mock_parse_property.assert_has_calls([call("prop1", "obj1")])
    assert res == expected_out

    # second match
    res = instance._parse_forwarded_outputs("obj2", mock_forwarded_outputs)
    mock_parse_property.assert_has_calls([call("prop1", "obj2")])
    assert res == expected_out


@patch("openstack_query.query_blocks.query_output.QueryOutput._parse_property")
def test_parse_forwarded_outputs_multiple_sets(mock_parse_property, instance):
    """
    Tests parse_forwarded_outputs() method - a set of many forwarded_outputs
    first one-to-many (singleton list), second many-to-one (list containing many items)
    """
    one_to_many_out = {"forwarded-prop1": "val1", "forwarded-prop2": "val2"}

    many_to_one_out1 = {"forwarded-prop3": "val3", "forwarded-prop4": "val4"}
    many_to_one_out2 = {"forwarded-prop3": "new-val", "forwarded-prop4": "new-val2"}

    mock_forwarded_outputs = {
        "prop1": {"prop_val1": [one_to_many_out]},
        "prop2": {"prop_val2": [many_to_one_out1, many_to_one_out2]},
    }

    mock_parse_property.side_effect = [
        # first item calls
        "prop_val1",
        "prop_val2",
        # second item calls
        "prop_val1",
        "prop_val2",
    ]
    # pylint:disable=protected-access

    # first item
    res = instance._parse_forwarded_outputs("obj1", mock_forwarded_outputs)
    mock_parse_property.assert_has_calls([call("prop1", "obj1"), call("prop2", "obj1")])
    assert res == {**one_to_many_out, **many_to_one_out1}

    # second item
    res = instance._parse_forwarded_outputs("obj1", mock_forwarded_outputs)
    mock_parse_property.assert_has_calls([call("prop1", "obj1"), call("prop2", "obj1")])
    assert res == {**one_to_many_out, **many_to_one_out2}


@patch("openstack_query.query_blocks.query_output.QueryOutput._parse_property")
def test_parse_forwarded_prop_value_not_found(mock_parse_property, instance):
    """
    Tests parse_forwarded_outputs() method
    where a prop_value is not found - raise error
    """
    mock_forwarded_outputs = {"prop1": {"prop-val1": ["outputs"]}}

    mock_parse_property.return_value = "invalid-prop"
    with pytest.raises(QueryChainingError):
        # pylint:disable=protected-access
        instance._parse_forwarded_outputs("obj1", mock_forwarded_outputs)


@patch("openstack_query.query_blocks.query_output.QueryOutput._parse_property")
def test_parse_forwarded_outputs_many_to_one(mock_parse_property, instance):
    """
    Tests parse_forwarded_outputs() method - where forwarded outputs expects duplicates
    cases where grouped results have a many-to-one relationship.
    i.e. finding Users mapped to Servers - many servers can be mapped to one user - so duplicates of same user ids
    are expected
    """
    expected_out1 = {"forwarded-prop1": "val1", "forwarded-prop2": "val2"}
    expected_out2 = {"forwarded-prop3": "val3", "forwarded-prop4": "val4"}

    mock_forwarded_outputs = {"prop1": {"prop_val1": [expected_out1, expected_out2]}}
    mock_parse_property.side_effect = ["prop_val1", "prop_val1"]
    # pylint:disable=protected-access

    # first duplicate - takes first item in list
    res = instance._parse_forwarded_outputs("obj1", mock_forwarded_outputs)
    assert res == expected_out1

    # second duplicate - takes second item in list
    res = instance._parse_forwarded_outputs("obj2", mock_forwarded_outputs)
    assert res == expected_out2

    mock_parse_property.assert_has_calls([call("prop1", "obj1"), call("prop1", "obj2")])


def test_reset(instance):
    """
    Tests reset function resets selected props
    """
    instance.reset()
    assert instance.selected_props == []
