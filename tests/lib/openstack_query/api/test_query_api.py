from unittest.mock import MagicMock, NonCallableMock, patch
import pytest

from openstack_query.api.query_api import QueryAPI

from exceptions.parse_query_error import ParseQueryError
from tests.lib.openstack_query.mocks.mocked_query_presets import MockQueryPresets
from tests.lib.openstack_query.mocks.mocked_props import MockProperties


@pytest.fixture(name="instance")
def instance_fixture():
    """
    Returns an instance to run tests with
    """
    res = QueryAPI(query_components=MagicMock())
    res.results_container = MagicMock()
    return res


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

    res = instance.select([MockProperties.PROP_1, MockProperties.PROP_2])
    mock_query_output.parse_select.assert_called_once_with(
        [MockProperties.PROP_1, MockProperties.PROP_2], select_all=False
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


def test_run_invalid_params(instance):
    """
    Tests run method - when neither cloud_account or from_subset given
    should raise an error
    """
    with pytest.raises(ParseQueryError):
        instance.run()


def test_run_from_subset(instance):
    """
    Tests run method with from subset params
    method should call executer.run_with_subset
    """
    mock_subset = NonCallableMock()

    client_filter = NonCallableMock()
    instance.builder.client_side_filters = [client_filter]

    fallback_filter = NonCallableMock()
    instance.builder.server_filter_fallback = [fallback_filter]
    instance.chainer.forwarded_info = None, None

    res = instance.run(from_subset=mock_subset)
    instance.executer.run_with_subset.assert_called_once_with(
        subset=mock_subset, client_side_filters=[client_filter, fallback_filter]
    )

    instance.executer.apply_forwarded_results.assert_not_called()
    assert res == instance


@patch("openstack_query.api.query_api.deepcopy")
def test_run_from_subset_with_chained_values(mock_deepcopy, instance):
    """
    Tests run method with from subset params and chained values
    method should call executer.run_with_subset and then executer.apply_forwarded_results
    """
    mock_subset = NonCallableMock()

    client_filter = NonCallableMock()
    instance.builder.client_side_filters = [client_filter]

    fallback_filter = NonCallableMock()
    instance.builder.server_filter_fallback = [fallback_filter]

    mock_link_prop = NonCallableMock()
    mock_forwarded_vals = NonCallableMock()
    instance.chainer.forwarded_info = mock_link_prop, mock_forwarded_vals

    res = instance.run(from_subset=mock_subset)

    instance.executer.run_with_subset.assert_called_once_with(
        subset=mock_subset, client_side_filters=[client_filter, fallback_filter]
    )

    instance.executer.apply_forwarded_results.assert_called_once_with(
        mock_link_prop, mock_deepcopy.return_value
    )
    mock_deepcopy.assert_called_once_with(mock_forwarded_vals)
    assert res == instance


def test_run_with_openstacksdk(instance):
    """
    Tests run method with cloud_account param
    method should call executer.run_with_openstacksdk
    """
    mock_cloud_account = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}

    instance.chainer.forwarded_info = None, None

    res = instance.run(cloud_account=mock_cloud_account, **mock_kwargs)
    instance.executer.run_with_openstacksdk.assert_called_once_with(
        cloud_account=mock_cloud_account,
        client_side_filters=instance.builder.client_side_filters,
        server_side_filters=instance.builder.server_side_filters,
        **mock_kwargs
    )
    instance.executer.apply_forwarded_results.assert_not_called()
    assert res == instance


@patch("openstack_query.api.query_api.deepcopy")
def test_run_with_openstacksdk_with_chained_values(mock_deepcopy, instance):
    """
    Tests run method with cloud_account param and chained values
    method should call executer.run_with_openstacksdk and then executer.apply_forwarded_results
    """
    mock_cloud_account = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}

    mock_link_prop = NonCallableMock()
    mock_forwarded_val = NonCallableMock()
    instance.chainer.forwarded_info = mock_link_prop, mock_forwarded_val

    res = instance.run(cloud_account=mock_cloud_account, **mock_kwargs)
    instance.executer.run_with_openstacksdk.assert_called_once_with(
        cloud_account=mock_cloud_account,
        client_side_filters=instance.builder.client_side_filters,
        server_side_filters=instance.builder.server_side_filters,
        **mock_kwargs
    )
    instance.executer.apply_forwarded_results.assert_called_once_with(
        mock_link_prop, mock_deepcopy.return_value
    )
    mock_deepcopy.assert_called_once_with(mock_forwarded_val)
    assert res == instance


def test_to_props(instance):
    """
    Tests that to_props method functions expectedly - with no extra params
    method should just return _query_results attribute when groups is None and flatten is false
    """
    mock_groups = NonCallableMock()
    mock_flatten = NonCallableMock()

    res = instance.to_props(mock_flatten, mock_groups)
    instance.results_container.parse_results.assert_called_once_with(
        instance.parser.run_parser
    )
    instance.output.to_props.assert_called_once_with(
        instance.results_container, mock_flatten, mock_groups
    )
    assert res == instance.output.to_props.return_value


def test_to_csv(instance):
    """
    Tests to_csv method, method should call results_container.parse_results and forward that result
    onto output.to_csv with given dir_path param
    """
    mock_dir_path = NonCallableMock()
    res = instance.to_csv(mock_dir_path)
    instance.results_container.parse_results.assert_called_once_with(
        instance.parser.run_parser
    )
    instance.output.to_csv.assert_called_once_with(
        instance.results_container, mock_dir_path
    )
    assert res == instance.output.to_csv.return_value


def test_to_objects(instance):
    """
    Tests that to_objects method functions expectedly - with no extra params
    method should just return _query_results_as_objects attribute when groups is None
    """
    mock_flatten = NonCallableMock()

    instance.executer.has_forwarded_results = False

    res = instance.to_objects(mock_flatten)
    instance.results_container.parse_results.assert_called_once_with(
        instance.parser.run_parser
    )
    instance.output.to_objects.assert_called_once_with(
        instance.results_container,
        mock_flatten,
    )
    assert res == instance.output.to_objects.return_value


def test_to_objects_with_forwarded_results(instance):
    """
    Tests that to_objects method - but where forwarded_results are given
    method should output a warning but continue as normal
    """
    mock_flatten = NonCallableMock()

    instance.executer.has_forwarded_results = True

    res = instance.to_objects(mock_flatten)
    instance.results_container.parse_results.assert_called_once_with(
        instance.parser.run_parser
    )
    instance.output.to_objects.assert_called_once_with(
        instance.results_container,
        mock_flatten,
    )
    assert res == instance.output.to_objects.return_value


def test_to_string(instance):
    """
    Tests that to_string method functions expectedly
    method should call QueryOutput object to_string() and return results
    """
    mock_groups = NonCallableMock()
    mock_title = NonCallableMock()
    mock_include_group_titles = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}

    instance.results_container = MagicMock()

    res = instance.to_string(
        mock_title, mock_groups, mock_include_group_titles, **mock_kwargs
    )
    instance.results_container.parse_results.assert_called_once_with(
        instance.parser.run_parser
    )
    instance.output.to_string.assert_called_once_with(
        instance.results_container,
        mock_title,
        mock_groups,
        mock_include_group_titles,
        **mock_kwargs
    )
    assert res == instance.output.to_string.return_value


def test_to_html(instance):
    """
    Tests that to_html method functions expectedly
    method should call QueryOutput object to_html() and return results
    """
    mock_groups = NonCallableMock()
    mock_title = NonCallableMock()
    mock_include_group_titles = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}

    res = instance.to_html(
        mock_title, mock_groups, mock_include_group_titles, **mock_kwargs
    )
    instance.results_container.parse_results.assert_called_once_with(
        instance.parser.run_parser
    )
    instance.output.to_html.assert_called_once_with(
        instance.results_container,
        mock_title,
        mock_groups,
        mock_include_group_titles,
        **mock_kwargs
    )
    assert res == instance.output.to_html.return_value


def test_sort_by(instance):
    """
    Tests that sort_by method functions expectedly
    method should call QueryParser object parse_sort_by() and return results
    """
    mock_sort_by = [("some-prop-enum", "ascending"), ("some-prop-enum-2", "descending")]
    res = instance.sort_by(mock_sort_by)
    instance.parser.parse_sort_by.assert_called_once_with(mock_sort_by)
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


def test_append_from(instance):
    """
    Tests that append_from method - should call run_append_from_query
    and martial results into results_container.apply_forwarded_results
    """
    mock_query_type = NonCallableMock()
    mock_cloud_account = NonCallableMock()
    mock_prop1 = NonCallableMock()
    mock_prop2 = NonCallableMock()

    mock_link_prop = NonCallableMock()
    mock_new_query_results = NonCallableMock()

    instance.chainer.run_append_from_query.return_value = (
        mock_link_prop,
        mock_new_query_results,
    )

    res = instance.append_from(
        mock_query_type, mock_cloud_account, [mock_prop1, mock_prop2]
    )
    instance.chainer.run_append_from_query.assert_called_once_with(
        instance, mock_query_type, mock_cloud_account, [mock_prop1, mock_prop2]
    )
    instance.results_container.apply_forwarded_results(
        mock_link_prop, mock_new_query_results
    )

    assert res == instance
