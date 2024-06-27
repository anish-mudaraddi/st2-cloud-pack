from unittest.mock import call, patch
import pytest

from enums.query.props.server_properties import ServerProperties
from enums.query.sort_order import SortOrder
from exceptions.parse_query_error import ParseQueryError

from openstack_query.query_blocks.query_sorter import QuerySorter
from tests.lib.openstack_query.mocks.mocked_props import MockProperties


@pytest.fixture(name="instance")
def instance_fixture():
    """
    Returns an instance with mocked prop_enum_cls inject
    """
    mock_prop_enum_cls = MockProperties
    return QuerySorter(prop_enum_cls=mock_prop_enum_cls)


@pytest.fixture(name="run_sort_by_runner")
def run_sort_by_runner_fixture(instance, mock_get_prop_mapping):
    """
    Fixture which runs run_sort_by with different test cases
    """

    def _run_sort_by_runner(obj_list, sort_by_specs, expected_list):
        """
        Method which runs sort_by with different inputs
        """
        instance.parse_sort_by(sort_by_specs)
        with patch.object(
            MockProperties, "get_prop_mapping", wraps=mock_get_prop_mapping
        ) as mock_get_prop_func:
            res = instance.run_sort_by(obj_list)
            assert [item.as_object() for item in res] == expected_list
            mock_get_prop_func.assert_has_calls(
                [call(sort_key) for sort_key, _ in reversed(sort_by_specs)]
            )

    return _run_sort_by_runner


def test_parse_sort_by_invalid(instance):
    """
    Tests parse_sort_by method works expectedly - raise error if property is invalid
    should raise ParseQueryError
    """
    with pytest.raises(ParseQueryError):
        instance.parse_sort_by([(ServerProperties.SERVER_ID, SortOrder.DESC)])


@pytest.mark.parametrize(
    "mock_sort_by_specs",
    [
        [("name", "asc")],
        [("id", "desc")],
    ],
)
def test_parse_sort_by_with_string_aliases(mock_sort_by_specs, mock_results_container):
    """
    Tests parse_sort_by accepts string aliases for prop and sort order
    """
    mock_as_object_vals = [
        {"name": "a", "id": 2},
        {"name": "c", "id": 4},
        {"name": "d", "id": 3},
        {"name": "b", "id": 1},
    ]
    mock_obj_list = mock_results_container(mock_as_object_vals)
    instance = QuerySorter(prop_enum_cls=ServerProperties)

    mock_string = mock_sort_by_specs[0][0]
    reverse = mock_sort_by_specs[0][1] == "desc"
    expected_list = sorted(
        mock_as_object_vals, key=lambda k: k[mock_string], reverse=reverse
    )
    instance.parse_sort_by(mock_sort_by_specs)
    res = instance.run_sort_by(mock_obj_list)
    assert [item.as_object() for item in res] == expected_list


@pytest.mark.parametrize(
    "mock_sort_by_specs",
    [
        [(MockProperties.PROP_1, SortOrder.ASC)],
        [(MockProperties.PROP_2, SortOrder.ASC)],
        [(MockProperties.PROP_1, SortOrder.DESC)],
        [(MockProperties.PROP_2, SortOrder.DESC)],
    ],
)
def test_run_sort_with_one_key(
    mock_sort_by_specs, run_sort_by_runner, mock_results_container
):
    """
    Tests that run_sort functions expectedly - with one sorting key
    Should call run_sort method which should get the appropriate sorting
    key lambda function and sort dict accordingly
    """
    mock_as_object_vals = [
        {"prop_1": "a", "prop_2": 2},
        {"prop_1": "c", "prop_2": 4},
        {"prop_1": "d", "prop_2": 3},
        {"prop_1": "b", "prop_2": 1},
    ]

    mock_obj_list = mock_results_container(mock_as_object_vals)

    # sorting by only one property so get first key in sort specs
    mock_enum = mock_sort_by_specs[0][0]
    reverse = mock_sort_by_specs[0][1].value
    mock_prop_name = mock_enum.name.lower()

    expected_list = sorted(
        mock_as_object_vals, key=lambda k: k[mock_prop_name], reverse=reverse
    )
    run_sort_by_runner(mock_obj_list, mock_sort_by_specs, expected_list)


@pytest.mark.parametrize(
    "mock_sort_by_specs, expected_list",
    [
        (
            [
                (MockProperties.PROP_1, SortOrder.ASC),
                (MockProperties.PROP_2, SortOrder.DESC),
            ],
            [
                {"prop_1": "a", "prop_2": 2},
                {"prop_1": "a", "prop_2": 1},
                {"prop_1": "b", "prop_2": 2},
                {"prop_1": "b", "prop_2": 1},
            ],
        ),
        (
            [
                (MockProperties.PROP_1, SortOrder.DESC),
                (MockProperties.PROP_2, SortOrder.ASC),
            ],
            [
                {"prop_1": "b", "prop_2": 1},
                {"prop_1": "b", "prop_2": 2},
                {"prop_1": "a", "prop_2": 1},
                {"prop_1": "a", "prop_2": 2},
            ],
        ),
        (
            [
                (MockProperties.PROP_2, SortOrder.ASC),
                (MockProperties.PROP_1, SortOrder.DESC),
            ],
            [
                {"prop_1": "b", "prop_2": 1},
                {"prop_1": "a", "prop_2": 1},
                {"prop_1": "b", "prop_2": 2},
                {"prop_1": "a", "prop_2": 2},
            ],
        ),
        (
            [
                (MockProperties.PROP_2, SortOrder.DESC),
                (MockProperties.PROP_1, SortOrder.ASC),
            ],
            [
                {"prop_1": "a", "prop_2": 2},
                {"prop_1": "b", "prop_2": 2},
                {"prop_1": "a", "prop_2": 1},
                {"prop_1": "b", "prop_2": 1},
            ],
        ),
    ],
)
def test_run_sort_with_multiple_key(
    mock_sort_by_specs, expected_list, run_sort_by_runner, mock_results_container
):
    """
    Tests that run_sort functions expectedly - with one sorting key
    Should call run_sort method which should get the appropriate sorting
    key lambda function and sort dict accordingly
    """
    mock_as_object_vals = [
        {"prop_1": "a", "prop_2": 1},
        {"prop_1": "b", "prop_2": 1},
        {"prop_1": "a", "prop_2": 2},
        {"prop_1": "b", "prop_2": 2},
    ]
    mock_obj_list = mock_results_container(mock_as_object_vals)
    run_sort_by_runner(mock_obj_list, mock_sort_by_specs, expected_list)


@pytest.mark.parametrize(
    "mock_sort_by_specs",
    [
        [(MockProperties.PROP_1, SortOrder.ASC)],
        [(MockProperties.PROP_1, SortOrder.DESC)],
    ],
)
def test_run_sort_with_boolean(
    mock_sort_by_specs, run_sort_by_runner, mock_results_container
):
    """
    Tests that run_sort functions expectedly - sorting by boolean
    Should call run_sort method which should get the appropriate sorting
    key lambda function and sort dict accordingly
    """
    mock_as_object_vals = [{"prop_1": False}, {"prop_1": True}]
    mock_obj_list = mock_results_container(mock_as_object_vals)
    mock_enum = mock_sort_by_specs[0][0]
    reverse = mock_sort_by_specs[0][1].value
    mock_prop_name = mock_enum.name.lower()

    expected_list = sorted(
        mock_as_object_vals, key=lambda k: k[mock_prop_name], reverse=reverse
    )
    run_sort_by_runner(mock_obj_list, mock_sort_by_specs, expected_list)
