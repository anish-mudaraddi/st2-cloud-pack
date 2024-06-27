from unittest.mock import patch, NonCallableMock, MagicMock
import pytest

from enums.query.query_presets import QueryPresetsString
from enums.query.sort_order import SortOrder
from workflows.search_by_regex import search_by_regex


@patch("workflows.search_by_regex.openstack_query")
@pytest.mark.parametrize(
    "output_type", ["to_html", "to_string", "to_objects", "to_props"]
)
def test_search_by_regex_minimal(mock_openstack_query, output_type):
    """
    Runs search_by_regex only providing required values
    """

    mock_query = MagicMock()
    mock_cloud_account = NonCallableMock()

    mock_openstack_query.MockQuery.return_value = mock_query
    params = {
        "cloud_account": mock_cloud_account,
        "query_type": "MockQuery",
        "property_to_search_by": NonCallableMock(),
        "output_type": output_type,
        "pattern": NonCallableMock(),
    }
    res = search_by_regex(**params)

    mock_query.select_all.assert_called_once()
    mock_query.where.assert_called_once_with(
        preset=QueryPresetsString.MATCHES_REGEX,
        prop=params["property_to_search_by"],
        args={"value": params["pattern"]},
    )
    mock_query.run.assert_called_once_with(mock_cloud_account)

    assert (
        res
        == {
            "to_html": mock_query.to_html.return_value,
            "to_string": mock_query.to_string.return_value,
            "to_objects": mock_query.to_objects.return_value,
            "to_props": mock_query.to_props.return_value,
        }[output_type]
    )


@patch("workflows.search_by_regex.openstack_query")
@pytest.mark.parametrize(
    "output_type", ["to_html", "to_string", "to_objects", "to_props"]
)
def test_search_by_regex_all(mock_openstack_query, output_type):
    """
    Runs search_by_regex providing all values
    """

    mock_query = MagicMock()
    mock_cloud_account = NonCallableMock()

    mock_openstack_query.MockQuery.return_value = mock_query
    params = {
        "cloud_account": mock_cloud_account,
        "query_type": "MockQuery",
        "property_to_search_by": NonCallableMock(),
        "output_type": output_type,
        "properties_to_select": ["prop1", "prop2"],
        "pattern": NonCallableMock(),
        "group_by": NonCallableMock(),
        "sort_by": ["prop1", "prop2"],
        "arg1": "val1",
        "arg2": "val2",
    }
    res = search_by_regex(**params)

    mock_query.select.assert_called_once_with(params["properties_to_select"])
    mock_query.where.assert_called_once_with(
        preset=QueryPresetsString.MATCHES_REGEX,
        prop=params["property_to_search_by"],
        args={"value": params["pattern"]},
    )
    mock_query.sort_by.assert_called_once_with(
        *[(p, SortOrder.DESC) for p in params["sort_by"]]
    )
    mock_query.group_by.assert_called_once_with(params["group_by"])
    mock_query.run.assert_called_once_with(
        params["cloud_account"], arg1="val1", arg2="val2"
    )

    assert (
        res
        == {
            "to_html": mock_query.to_html.return_value,
            "to_string": mock_query.to_string.return_value,
            "to_objects": mock_query.to_objects.return_value,
            "to_props": mock_query.to_props.return_value,
        }[output_type]
    )
