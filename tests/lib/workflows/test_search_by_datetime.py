from unittest.mock import patch, NonCallableMock, MagicMock
import pytest

from enums.query.sort_order import SortOrder
from workflows.search_by_datetime import search_by_datetime


@patch("workflows.search_by_datetime.openstack_query")
@patch("workflows.search_by_datetime.QueryPresetsDateTime")
@pytest.mark.parametrize(
    "output_type", ["to_html", "to_string", "to_objects", "to_props"]
)
def test_search_by_datetime_minimal(
    mock_preset_enum, mock_openstack_query, output_type
):
    """
    Runs search_by_datetime only providing required values
    """

    mock_query = MagicMock()
    mock_cloud_account = NonCallableMock()

    mock_openstack_query.MockQuery.return_value = mock_query
    params = {
        "cloud_account": mock_cloud_account,
        "query_type": "MockQuery",
        "search_mode": NonCallableMock(),
        "property_to_search_by": NonCallableMock(),
        "output_type": output_type,
        "days": 1,
    }
    res = search_by_datetime(**params)

    mock_query.select_all.assert_called_once()
    mock_query.where.assert_called_once_with(
        preset=mock_preset_enum.from_string.return_value,
        prop=params["property_to_search_by"],
        args={
            "days": 1,
            "hours": 0,
            "minutes": 0,
            "seconds": 0,
        },
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


def test_search_by_datetime_errors_when_args_all_zero():
    """
    test that search_by_datetime errors when days, hours, minutes and seconds are all set to zero
    """
    with pytest.raises(RuntimeError):
        search_by_datetime(
            cloud_account=NonCallableMock(),
            query_type=NonCallableMock(),
            search_mode=NonCallableMock(),
            property_to_search_by=NonCallableMock(),
            output_type=NonCallableMock(),
        )


@patch("workflows.search_by_datetime.openstack_query")
@patch("workflows.search_by_datetime.QueryPresetsDateTime")
@pytest.mark.parametrize(
    "output_type", ["to_html", "to_string", "to_objects", "to_props"]
)
def test_search_by_datetime_all(mock_preset_enum, mock_openstack_query, output_type):
    """
    Runs search_by_datetime providing all available params
    """

    mock_query = MagicMock()
    mock_cloud_account = NonCallableMock()

    mock_openstack_query.MockQuery.return_value = mock_query
    params = {
        "cloud_account": mock_cloud_account,
        "query_type": "MockQuery",
        "search_mode": NonCallableMock(),
        "property_to_search_by": NonCallableMock(),
        "output_type": output_type,
        "properties_to_select": ["prop1", "prop2"],
        "days": 1,
        "group_by": NonCallableMock(),
        "sort_by": ["prop1", "prop2"],
        "arg1": "val1",
        "arg2": "val2",
    }
    res = search_by_datetime(**params)

    mock_query.select.assert_called_once_with(params["properties_to_select"])
    mock_query.where.assert_called_once_with(
        preset=mock_preset_enum.from_string.return_value,
        prop=params["property_to_search_by"],
        args={
            "days": 1,
            "hours": 0,
            "minutes": 0,
            "seconds": 0,
        },
    )
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
