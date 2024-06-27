from unittest.mock import patch, NonCallableMock, MagicMock
import pytest

from enums.query.sort_order import SortOrder
from workflows.list_all_openstack import list_all_openstack


@patch("workflows.list_all_openstack.openstack_query")
@pytest.mark.parametrize(
    "output_type", ["to_html", "to_string", "to_objects", "to_props"]
)
def test_list_all_openstack_minimal(mock_openstack_query, output_type):
    """
    Runs list_all_openstack only providing required values
    """

    mock_query = MagicMock()
    mock_cloud_account = NonCallableMock()

    mock_openstack_query.MockQuery.return_value = mock_query

    res = list_all_openstack(
        cloud_account=mock_cloud_account,
        query_type="MockQuery",
        output_type=output_type,
    )

    mock_query.select_all.assert_called_once()
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


@patch("workflows.list_all_openstack.openstack_query")
@pytest.mark.parametrize(
    "output_type", ["to_html", "to_string", "to_objects", "to_props"]
)
def test_list_all_openstack_all(mock_openstack_query, output_type):
    """
    Runs list_all_openstack only providing all values
    """
    mock_query = MagicMock()
    mock_openstack_query.MockQuery.return_value = mock_query

    params = {
        "cloud_account": NonCallableMock(),
        "query_type": "MockQuery",
        "properties_to_select": ["prop1", "prop2"],
        "output_type": output_type,
        "group_by": NonCallableMock(),
        "sort_by": ["prop1", "prop2"],
        "arg1": "val1",
        "arg2": "val2",
    }

    res = list_all_openstack(**params)

    mock_query.select.assert_called_once_with(params["properties_to_select"])
    mock_query.sort_by.assert_called_once_with(
        [(p, SortOrder.DESC) for p in params["sort_by"]]
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
