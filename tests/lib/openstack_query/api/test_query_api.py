from unittest.mock import MagicMock, NonCallableMock, patch
import pytest

from openstack_query.api.query_api import QueryAPI

from exceptions.parse_query_error import ParseQueryError
from tests.lib.openstack_query.mocks.mocked_query_presets import MockQueryPresets
from tests.lib.openstack_query.mocks.mocked_props import MockProperties

# pylint:disable=protected-access


@pytest.fixture(name="instance")
def instance_fixture():
    """
    Returns an instance to run tests with
    """
    return QueryAPI(query_components=MagicMock())


@pytest.fixture(name="run_with_test_case_with_subset")
def run_with_test_case_with_subset_fixture(instance):
    """
    Fixture for running run() with a subset
    """

    def _run_with_test_case(mock_kwargs):
        """
        Runs a test case for the run() method
        """
        mock_query_results = ("object-list", "property-list")
        instance.executer.run_query.return_value = mock_query_results
        instance.builder.client_side_filters = ["client-filters"]
        instance.builder.server_filter_fallback = ["fallback-client-filters"]
        instance.builder.server_side_filters = ["server-filters"]

        if not mock_kwargs:
            mock_kwargs = {}

        res = instance.run("test-account", ["item1", "item2"], **mock_kwargs)
        instance.executer.run_query.assert_called_once_with(
            cloud_account="test-account", from_subset=["item1", "item2"], **mock_kwargs
        )

        # test that data is marshalled correctly to executer
        # - this differs based on if from_subset is given
        client_filters = (
            instance.builder.client_side_filters
            + instance.builder.server_filter_fallback
        )
        server_filters = None

        assert instance.executer.client_side_filters == client_filters
        assert instance.executer.server_side_filters == server_filters
        assert res == instance

    return _run_with_test_case


@pytest.fixture(name="run_with_test_case")
def run_with_test_case_fixture(instance):
    """
    Fixture for running run() with various test arguments
    """

    def _run_with_test_case(data_subset, mock_kwargs):
        """
        Runs a test case for the run() method
        """
        mock_query_results = ("object-list", "property-list")
        instance.executer.run_query.return_value = mock_query_results
        instance.builder.client_side_filters = ["client-filters"]
        instance.builder.server_filter_fallback = ["fallback-client-filters"]
        instance.builder.server_side_filters = ["server-filters"]

        if not mock_kwargs:
            mock_kwargs = {}

        res = instance.run("test-account", data_subset, **mock_kwargs)
        instance.executer.run_query.assert_called_once_with(
            cloud_account="test-account", from_subset=data_subset, **mock_kwargs
        )

        # test that data is marshalled correctly to executer
        # - this differs based on if from_subset is given
        client_filters = instance.builder.client_side_filters
        server_filters = instance.builder.server_side_filters

        assert instance.executer.client_side_filters == client_filters
        assert instance.executer.server_side_filters == server_filters
        assert res == instance

    return _run_with_test_case


def test_select_invalid(instance):
    """
    Tests select method works expectedly - with no inputs
    method raises ParseQueryError when given no properties
    """
    with pytest.raises(ParseQueryError):
        instance.select()


def test_select_with_one_prop(instance):
    """
    Tests select method works expectedly - with one prop
    method should forward prop to parse_select in QueryOutput object
    """
    mock_query_output = MagicMock()
    instance.output = mock_query_output

    res = instance.select(MockProperties.PROP_1)
    mock_query_output.parse_select.assert_called_once_with(
        MockProperties.PROP_1, select_all=False
    )
    assert res == instance


def test_select_with_many_props(instance):
    """
    Tests select method works expectedly - with multiple prop
    method should forward props to parse_select in QueryOutput object
    """
    mock_query_output = MagicMock()
    instance.output = mock_query_output

    res = instance.select(MockProperties.PROP_1, MockProperties.PROP_2)
    mock_query_output.parse_select.assert_called_once_with(
        MockProperties.PROP_1, MockProperties.PROP_2, select_all=False
    )
    assert res == instance


def test_select_all(instance):
    """
    Tests select all method works expectedly
    method should call parse_select in QueryOutput object
    """
    mock_query_output = MagicMock()
    instance.output = mock_query_output
    res = instance.select_all()
    mock_query_output.parse_select.assert_called_once_with(select_all=True)
    assert res == instance


def test_where_no_kwargs(instance):
    """
    Tests that where method works expectedly
    method should forward to parse_where in QueryBuilder object - with no kwargs given
    """
    mock_query_builder = MagicMock()
    instance.builder = mock_query_builder

    res = instance.where(MockQueryPresets.ITEM_1, MockProperties.PROP_1)
    mock_query_builder.parse_where.assert_called_once_with(
        MockQueryPresets.ITEM_1, MockProperties.PROP_1, {}
    )
    assert res == instance


def test_where_with_kwargs(instance):
    """
    Tests that where method works expectedly
    method should forward to parse_where in QueryBuilder object - with kwargs given
    """
    mock_query_builder = MagicMock()
    instance.builder = mock_query_builder
    res = instance.where(
        MockQueryPresets.ITEM_2, MockProperties.PROP_2, arg1="val1", arg2="val2"
    )
    mock_query_builder.parse_where.assert_called_once_with(
        MockQueryPresets.ITEM_2,
        MockProperties.PROP_2,
        {"arg1": "val1", "arg2": "val2"},
    )
    assert res == instance


def test_run_with_optional_params(run_with_test_case_with_subset):
    """
    Tests that run method works expectedly - with subset meta_params kwargs
    method should get client_side and server_side filters and forward them to query runner object

    """
    run_with_test_case_with_subset(mock_kwargs=None)


def test_run_with_kwargs(run_with_test_case):
    """
    Tests that run method works expectedly - with subset kwargs
    method should get client_side and server_side filters and forward them to query runner object

    """
    run_with_test_case(data_subset=None, mock_kwargs={"arg1": "val1", "arg2": "val2"})


def test_run_with_nothing(run_with_test_case):
    """
    Tests that run method works expectedly - with subset kwargs
    method should get client_side and server_side filters and forward them to query runner object

    """
    run_with_test_case(None, None)


def test_run_with_kwargs_and_subset(run_with_test_case_with_subset):
    """
    Tests that run method works expectedly - with subset kwargs
    method should get client_side and server_side filters and forward them to query runner object

    """
    run_with_test_case_with_subset(
        mock_kwargs={"arg1": "val1", "arg2": "val2"},
    )


def test_to_props(instance):
    """
    Tests that to_props method functions expectedly - with no extra params
    method should just return _query_results attribute when groups is None and flatten is false
    """
    instance.executer.parse_results.return_value = "", "parsed-list"
    assert instance.to_props() == "parsed-list"


def test_to_objects(instance):
    """
    Tests that to_objects method functions expectedly - with no extra params
    method should just return _query_results_as_objects attribute when groups is None
    """
    # pylint: disable=protected-access
    instance.output.forwarded_outputs = {}
    instance.executer.parse_results.return_value = "object-list", ""
    assert instance.to_objects() == "object-list"


def test_to_objects_forwarded_outputs_warning(instance):
    """
    Tests that to_objects method functions expectedly
    prints warning when forwarded_outputs is not empty
    """
    # pylint: disable=protected-access
    instance.output.forwarded_outputs = {"out1": "val1"}

    # should just continue running as normal after printing warning
    instance.executer.parse_results.return_value = "object-list", ""
    assert instance.to_objects() == "object-list"


def test_to_props_flatten_true(instance):
    """
    Tests that to_props method functions expectedly
    method should call output.flatten() with query_results
    """
    instance.executer.parse_results.return_value = "", "parsed-list"
    res = instance.to_props(flatten=True)
    instance.output.flatten.assert_called_once_with("parsed-list")
    assert res == instance.output.flatten.return_value


def test_to_props_with_groups_not_dict(instance):
    """
    Tests that to_props method functions expectedly
    method should raise error when given group and results are not dict
    """
    instance.executer.parse_results.return_value = "", ["obj1", "obj2"]
    with pytest.raises(ParseQueryError):
        instance.to_props(groups=["group1", "group2"])


def test_to_objects_with_groups_not_dict(instance):
    """
    Tests that to_objects method functions expectedly
    method should raise error when given group and results are not dict
    """
    instance.output.forwarded_outputs = {}
    instance.executer.parse_results.return_value = "", ["obj1", "obj2"]
    with pytest.raises(ParseQueryError):
        instance.to_objects(groups=["group1", "group2"])


def test_to_props_groups_dict(instance):
    """
    Tests that to_props method functions expectedly
    method should return subset of results which match keys (groups) given
    """
    mock_query_results = {
        "group1": ["result1", "result2"],
        "group2": ["result3", "result4"],
    }
    instance.executer.parse_results.return_value = "", mock_query_results
    res = instance.to_props(groups=["group1"])
    assert res == {"group1": mock_query_results["group1"]}


def test_to_objects_groups_dict(instance):
    """
    Tests that to_objects method functions expectedly
    method should return subset of results which match keys (groups) given
    """
    instance.output.forwarded_outputs = {}
    mock_query_results = {
        "group1": ["obj1", "obj2"],
        "group2": ["obj3", "obj4"],
    }
    instance.executer.parse_results.return_value = mock_query_results, ""
    res = instance.to_objects(groups=["group1"])
    assert res == {"group1": mock_query_results["group1"]}


def test_to_props_group_not_valid(instance):
    """
    Tests that to_props method functions expectedly
    method should raise error if group specified is not a key in results
    """
    mock_query_results = {
        "group1": ["result1", "result2"],
        "group2": ["result3", "result4"],
    }
    instance.executer.parse_results.return_value = "", mock_query_results
    with pytest.raises(ParseQueryError):
        instance.to_props(groups=["group3"])


def test_to_objects_group_not_valid(instance):
    """
    Tests that to_objects method functions expectedly
    method should raise error if group specified is not a key in results
    """
    instance.output.forwarded_outputs = {}
    mock_query_results = {
        "group1": ["result1", "result2"],
        "group2": ["result3", "result4"],
    }
    instance.executer.parse_results.return_value = mock_query_results, ""
    with pytest.raises(ParseQueryError):
        instance.to_objects(groups=["group3"])


def test_to_string(instance):
    """
    Tests that to_string method functions expectedly
    method should call QueryOutput object to_string() and return results
    """
    instance.executer.parse_results.return_value = "", "parsed-list"
    assert instance.to_string() == instance.output.to_string.return_value
    instance.output.to_string.assert_called_once_with("parsed-list", None, None)


def test_to_html(instance):
    """
    Tests that to_html method functions expectedly
    method should call QueryOutput object to_html() and return results
    """
    instance.executer.parse_results.return_value = "", "parsed-list"
    assert instance.to_html() == instance.output.to_html.return_value
    instance.output.to_html.assert_called_once_with("parsed-list", None, None)


def test_sort_by(instance):
    """
    Tests that sort_by method functions expectedly
    method should call QueryParser object parse_sort_by() and return results
    """
    mock_sort_by = [("some-prop-enum", False), ("some-prop-enum-2", True)]
    res = instance.sort_by(*mock_sort_by)
    instance.parser.parse_sort_by.assert_called_once_with(*mock_sort_by)
    assert res == instance


def test_group_by(instance):
    """
    Tests that group_by method functions expectedly
    method should call QueryParser object parse_group_by() and return results
    """
    mock_group_by = "some-prop-enum"
    mock_group_ranges = {"group1": ["val1", "val2"], "group2": ["val3"]}
    mock_include_ungrouped_results = False
    instance.parser.group_by = None

    res = instance.group_by(
        mock_group_by, mock_group_ranges, mock_include_ungrouped_results
    )
    instance.parser.parse_group_by.assert_called_once_with(
        mock_group_by, mock_group_ranges, mock_include_ungrouped_results
    )
    assert res == instance


def test_then(instance):
    """
    Tests that then method forwards to chainer parse_then method and return results
    """
    mock_query_type = NonCallableMock()
    keep_previous_results = NonCallableMock()
    res = instance.then(mock_query_type, keep_previous_results)
    instance.chainer.parse_then.assert_called_once_with(
        instance, mock_query_type, keep_previous_results
    )
    assert res == instance.chainer.parse_then.return_value


@patch("openstack_query.api.query_api.QueryAPI.then")
@patch("openstack_query.api.query_api.QueryTypes")
def test_append_from(mock_query_types_cls, mock_then, instance):
    """
    Tests that append_from method creates new query
    """
    mock_new_query = MagicMock()
    mock_cloud_account = NonCallableMock()
    mock_query_type = "query-type"

    mock_props = ["prop1", "prop2", "prop3"]
    instance.chainer.get_link_props.return_value = ("current-prop", "link-prop")
    mock_then.return_value = mock_new_query

    res = instance.append_from(mock_query_type, mock_cloud_account, *mock_props)
    mock_query_types_cls.from_string.assert_called_once_with(mock_query_type)
    mock_then.assert_called_once_with(
        mock_query_types_cls.from_string.return_value, keep_previous_results=False
    )

    mock_new_query.select.assert_called_once_with(*mock_props)
    mock_new_query.run.assert_called_once_with(mock_cloud_account)
    instance.chainer.get_link_props.assert_called_once_with(
        mock_query_types_cls.from_string.return_value
    )
    mock_new_query.group_by.assert_called_once_with("link-prop")
    mock_new_query.to_props.assert_called_once()
    instance.output.update_forwarded_outputs.assert_called_once_with(
        "current-prop", mock_new_query.to_props.return_value
    )
    assert res == instance


def test_reset(instance):
    """
    tests reset() function works properly
    should reset the query user-defined config back to defaults
    select(), where(), group_by(), sort_by() must all be reset
    """
    res = instance.reset()
    instance.builder.reset.assert_called_once()
    instance.output.reset.assert_called_once()
    instance.parser.reset.assert_called_once()
    instance.executer.reset.assert_not_called()
    assert res == instance


def test_reset_hard(instance):
    """
    Tests reset(hard=True) - should also reset run()
    """
    res = instance.reset(hard=True)
    instance.builder.reset.assert_called_once()
    instance.output.reset.assert_called_once()
    instance.parser.reset.assert_called_once()
    instance.executer.reset.assert_called_once()
    assert res == instance
