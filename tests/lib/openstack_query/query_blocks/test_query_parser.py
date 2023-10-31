from unittest.mock import MagicMock, call, patch
import pytest

from enums.query.props.server_properties import ServerProperties
from enums.query.sort_order import SortOrder
from openstack_query.query_blocks.query_parser import QueryParser
from exceptions.parse_query_error import ParseQueryError

from tests.lib.openstack_query.mocks.mocked_props import MockProperties


@pytest.fixture(name="instance")
def instance_fixture():
    """
    Returns an instance with mocked prop_enum_cls inject
    """
    mock_prop_enum_cls = MockProperties
    return QueryParser(prop_enum_cls=mock_prop_enum_cls)


@pytest.fixture(name="mock_get_prop_mapping")
def get_prop_mapping_fixture():
    """
    Returns a mocked get_prop_mapping function
    """

    def _mock_get_prop_mapping(mock_prop: MockProperties):
        """
        Stubs the get_prop_mapping method - it now takes a property enum and returns <prop_enum>.name.lower()
        :param mock_prop: property enum passed to get_prop_mapping
        """
        return MagicMock(wraps=lambda obj, prop=mock_prop: obj[prop.name.lower()])

    return _mock_get_prop_mapping


@pytest.fixture(name="run_sort_by_tests")
def run_sort_by_tests_fixture(instance, mock_get_prop_mapping):
    """
    Fixture which runs sort_by with different test cases
    """

    def _run_sort_by_tests(obj_list, sort_by_specs, expected_list):
        """
        Method which runs sort_by with different inputs
        """
        instance.sort_by = sort_by_specs
        with patch.object(
            MockProperties, "get_prop_mapping", wraps=mock_get_prop_mapping
        ) as mock_get_prop_func:
            # pylint:disable=protected-access
            res = instance._run_sort(obj_list)
            assert res == expected_list
            mock_get_prop_func.assert_has_calls(
                [call(sort_key) for sort_key in reversed(sort_by_specs.keys())]
            )

    return _run_sort_by_tests


def test_group_by(instance):
    """
    Tests that property functions group_by work
    """
    instance.group_by = MockProperties.PROP_1
    assert instance.group_by == MockProperties.PROP_1


def test_sort_by(instance):
    """
    Tests that property functions sort_by work
    """
    instance.sort_by = {MockProperties.PROP_1: True}
    assert instance.sort_by == {MockProperties.PROP_1: True}


def test_parse_sort_by_one_key(instance):
    """
    Tests parse_sort_by method works expectedly - one sort-by key
    should call check_prop_valid and add it to sort_by attribute
    """
    instance.parse_sort_by((MockProperties.PROP_1, SortOrder.ASC))
    assert instance.sort_by == {MockProperties.PROP_1: False}


def test_parse_sort_by_many_keys(instance):
    """
    Tests parse_sort_by method works expectedly - two sort-by keys
    should call check_prop_valid and add it to sort_by attribute
    """
    instance.parse_sort_by(
        (MockProperties.PROP_1, SortOrder.ASC), (MockProperties.PROP_2, SortOrder.DESC)
    )
    assert instance.sort_by == {
        MockProperties.PROP_1: False,
        MockProperties.PROP_2: True,
    }


def test_parse_sort_by_invalid(instance):
    """
    Tests parse_sort_by method works expectedly - raise error if property is invalid
    should raise ParseQueryError
    """
    with pytest.raises(ParseQueryError):
        instance.parse_sort_by((ServerProperties.SERVER_ID, True))


def test_parse_group_by_no_ranges(instance):
    """
    Tests parse_group_by functions expectedly - with no ranges
    Should simply set the group_by property as prop given
    """
    instance.parse_group_by(MockProperties.PROP_1)
    assert instance.group_by == MockProperties.PROP_1


@patch("openstack_query.query_blocks.query_parser.QueryParser._parse_group_ranges")
def test_parse_group_by_with_group_ranges(mock_parse_group_ranges, instance):
    """
    Tests parse_group_by functions expectedly - with group ranges
    Should set group_by and call parse_group_ranges
    """
    mock_group_ranges = {"group1": ["val1", "val2", "val3"], "group2": ["val4"]}
    instance.parse_group_by(MockProperties.PROP_1, mock_group_ranges)
    assert instance.group_by == MockProperties.PROP_1
    mock_parse_group_ranges.assert_called_once_with(mock_group_ranges)


@patch("openstack_query.query_blocks.query_parser.QueryParser._parse_group_ranges")
@patch(
    "openstack_query.query_blocks.query_parser.QueryParser._add_include_missing_group"
)
def test_parse_group_by_with_group_ranges_and_include_missing(
    mock_add_include_missing_group, mock_parse_group_ranges, instance
):
    """
    Tests parse_group_by functions expectedly - with group ranges
    Should set group_by and call parse_group_ranges
    """
    mock_group_ranges = {"group1": ["val1", "val2", "val3"], "group2": ["val4"]}
    instance.parse_group_by(
        MockProperties.PROP_1, mock_group_ranges, include_missing=True
    )
    assert instance.group_by == MockProperties.PROP_1
    mock_parse_group_ranges.assert_called_once_with(mock_group_ranges)
    mock_add_include_missing_group.assert_called_once_with(mock_group_ranges)


def test_run_parse_group_ranges(instance, mock_get_prop_mapping):
    """
    Tests parse_group_ranges functions expectedly
    Should setup groups based on given group mappings
    """
    mock_group_by = MockProperties.PROP_1
    instance.group_by = mock_group_by
    mock_group_ranges = {"group1": ["val1", "val2", "val3"], "group2": ["val4"]}

    with patch.object(
        MockProperties, "get_prop_mapping", wraps=mock_get_prop_mapping
    ) as mock_get_prop_func:
        # pylint:disable=protected-access
        instance._parse_group_ranges(group_ranges=mock_group_ranges)
        mock_get_prop_func.assert_called_once_with(mock_group_by)

    assert instance.group_mappings

    assert instance.group_mappings["group1"]({"prop_1": "val1"})
    assert not instance.group_mappings["group2"]({"prop_1": "val1"})


def test_add_include_missing_group(instance, mock_get_prop_mapping):
    """
    Tests add_include_missing_group functions expectedly
    Should create an extra "ungrouped results" group which includes values
    not already specified in any other group
    """
    mock_group_by = MockProperties.PROP_1
    instance.group_by = mock_group_by
    mock_group_ranges = {"group1": ["val1", "val2", "val3"], "group2": ["val4"]}

    with patch.object(
        MockProperties, "get_prop_mapping", wraps=mock_get_prop_mapping
    ) as mock_get_prop_func:
        # pylint:disable=protected-access
        instance._add_include_missing_group(mock_group_ranges)
        mock_get_prop_func.assert_called_once_with(mock_group_by)

    assert instance.group_mappings["ungrouped results"]({"prop_1": "val5"})
    assert not instance.group_mappings["ungrouped results"]({"prop_1": "val1"})
    assert not instance.group_mappings["ungrouped results"]({"prop_1": "val4"})


@patch("openstack_query.query_blocks.query_parser.QueryParser._run_sort")
def test_run_parser_with_sort_by(mock_run_sort, instance):
    """
    Tests that run_parser functions expectedly - when giving only sort_by
    Should call run_sort method, and return result
    """
    instance.sort_by = {MockProperties.PROP_1: False}
    instance.group_by = None
    instance.group_mappings = {}

    mock_run_sort.return_value = "sort-out"
    mock_obj_list = ["obj1", "obj2", "obj3"]
    res = instance.run_parser(mock_obj_list)

    assert res == "sort-out"
    mock_run_sort.assert_called_once_with(mock_obj_list)


@patch("openstack_query.query_blocks.query_parser.QueryParser._run_group_by")
def test_run_parser_no_sort_with_group_mappings(mock_run_group_by, instance):
    """
    Tests that run_parser functions expectedly - when giving group_mappings
    Should call run_group_by with group mappings and return
    """
    instance.sort_by = {}
    instance.group_by = MockProperties.PROP_1
    instance.group_mappings = {"group1": "some-mapping_func"}

    mock_obj_list = ["obj1", "obj2", "obj3"]
    mock_run_group_by.return_value = "group-out"
    instance.group_by = MockProperties.PROP_1

    res = instance.run_parser(mock_obj_list)
    assert res == "group-out"
    mock_run_group_by.assert_called_once_with(mock_obj_list)


@patch("openstack_query.query_blocks.query_parser.QueryParser._run_sort")
@patch("openstack_query.query_blocks.query_parser.QueryParser._run_group_by")
def test_run_parser_with_sort_and_group(mock_run_group_by, mock_run_sort, instance):
    """
    Tests that run_parser functions expectedly - when giving both group_by and sort_by
    Should call run_sort method and then run_group_by on that output, then return
    """
    instance.sort_by = {MockProperties.PROP_1: False}
    instance.group_by = MockProperties.PROP_1
    instance.group_mappings = {"group1": "some-mapping_func"}
    mock_obj_list = ["obj1", "obj2", "obj3"]

    mock_run_group_by.return_value = "group-out"
    mock_run_sort.return_value = "sort-out"

    res = instance.run_parser(mock_obj_list)
    assert res == "group-out"
    mock_run_sort.assert_called_once_with(mock_obj_list)
    mock_run_group_by.assert_called_once_with("sort-out")


@pytest.mark.parametrize(
    "mock_sort_by_specs",
    [
        {MockProperties.PROP_1: False},
        {MockProperties.PROP_1: True},
        {MockProperties.PROP_2: False},
        {MockProperties.PROP_2: True},
    ],
)
def test_run_sort_with_one_key(mock_sort_by_specs, run_sort_by_tests):
    """
    Tests that run_sort functions expectedly - with one sorting key
    Should call run_sort method which should get the appropriate sorting
    key lambda function and sort dict accordingly
    """

    mock_obj_list = [
        {"prop_1": "a", "prop_2": 2},
        {"prop_1": "c", "prop_2": 4},
        {"prop_1": "d", "prop_2": 3},
        {"prop_1": "b", "prop_2": 1},
    ]

    # sorting by only one property so get first key in sort specs
    mock_enum = list(mock_sort_by_specs.keys())[0]
    reverse = mock_sort_by_specs[mock_enum]
    mock_prop_name = mock_enum.name.lower()
    expected_list = sorted(
        mock_obj_list, key=lambda k: k[mock_prop_name], reverse=reverse
    )
    run_sort_by_tests(mock_obj_list, mock_sort_by_specs, expected_list)


@pytest.mark.parametrize(
    "mock_sort_by_specs, expected_list",
    [
        (
            {MockProperties.PROP_1: False, MockProperties.PROP_2: True},
            [
                {"prop_1": "a", "prop_2": 2},
                {"prop_1": "a", "prop_2": 1},
                {"prop_1": "b", "prop_2": 2},
                {"prop_1": "b", "prop_2": 1},
            ],
        ),
        (
            {MockProperties.PROP_1: True, MockProperties.PROP_2: False},
            [
                {"prop_1": "b", "prop_2": 1},
                {"prop_1": "b", "prop_2": 2},
                {"prop_1": "a", "prop_2": 1},
                {"prop_1": "a", "prop_2": 2},
            ],
        ),
        (
            {MockProperties.PROP_2: False, MockProperties.PROP_1: True},
            [
                {"prop_1": "b", "prop_2": 1},
                {"prop_1": "a", "prop_2": 1},
                {"prop_1": "b", "prop_2": 2},
                {"prop_1": "a", "prop_2": 2},
            ],
        ),
        (
            {MockProperties.PROP_2: True, MockProperties.PROP_1: False},
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
    mock_sort_by_specs, expected_list, run_sort_by_tests
):
    """
    Tests that run_sort functions expectedly - with one sorting key
    Should call run_sort method which should get the appropriate sorting
    key lambda function and sort dict accordingly
    """

    mock_obj_list = [
        {"prop_1": "a", "prop_2": 1},
        {"prop_1": "b", "prop_2": 1},
        {"prop_1": "a", "prop_2": 2},
        {"prop_1": "b", "prop_2": 2},
    ]
    run_sort_by_tests(mock_obj_list, mock_sort_by_specs, expected_list)


@pytest.mark.parametrize(
    "mock_sort_by_specs",
    [{MockProperties.PROP_1: False}, {MockProperties.PROP_1: True}],
)
def test_run_sort_with_boolean(mock_sort_by_specs, instance, run_sort_by_tests):
    """
    Tests that run_sort functions expectedly - sorting by boolean
    Should call run_sort method which should get the appropriate sorting
    key lambda function and sort dict accordingly
    """
    mock_obj_list = [
        {"prop_1": False},
        {"prop_1": True},
    ]
    instance.sort_by = mock_sort_by_specs
    mock_enum = list(mock_sort_by_specs.keys())[0]
    reverse = mock_sort_by_specs[mock_enum]
    mock_prop_name = mock_enum.name.lower()

    expected_list = sorted(
        mock_obj_list, key=lambda k: k[mock_prop_name], reverse=reverse
    )
    run_sort_by_tests(mock_obj_list, mock_sort_by_specs, expected_list)


@pytest.mark.parametrize(
    "mock_group_by, expected_out",
    [
        (
            MockProperties.PROP_1,
            {
                "a": [
                    {"prop_1": "a", "prop_2": 1},
                    {"prop_1": "a", "prop_2": 3},
                ],
                "b": [{"prop_1": "b", "prop_2": 2}],
            },
        ),
        (
            MockProperties.PROP_2,
            {
                1: [{"prop_1": "a", "prop_2": 1}],
                2: [{"prop_1": "b", "prop_2": 2}],
                3: [{"prop_1": "a", "prop_2": 3}],
            },
        ),
    ],
)
def test_build_unique_val_groups(
    mock_group_by, expected_out, instance, mock_get_prop_mapping
):
    """
    Tests that build_unique_val_groups method functions expectedly
    method should find all unique values for a test object list for a given property and create appropriate
    group_ranges to be used for group-by
    """

    obj_list = [
        {"prop_1": "a", "prop_2": 1},
        {"prop_1": "b", "prop_2": 2},
        {"prop_1": "a", "prop_2": 3},
    ]
    instance.group_by = mock_group_by

    with patch.object(
        MockProperties, "get_prop_mapping", wraps=mock_get_prop_mapping
    ) as mock_get_prop_func:
        # pylint:disable=protected-access
        res = instance._build_unique_val_groups(obj_list)
        assert res.keys() == expected_out.keys()
        mock_get_prop_func.assert_called_once_with(mock_group_by)

    # now that we have the group mappings - check that using them produces expected results
    grouped_out = {
        name: [item for item in obj_list if map_func(item)]
        for name, map_func in res.items()
    }
    assert grouped_out == expected_out


@patch("openstack_query.query_blocks.query_parser.QueryParser._build_unique_val_groups")
def test_run_group_by_no_group_mappings(mock_build_unique_val_groups, instance):
    """
    Tests run group_by method functions expectedly - when using no group mappings
    Should call build_unique_val_group and use the mappings returned to apply onto given object list
    """
    instance.group_mappings = {}
    instance.group_by = MockProperties.PROP_1

    mock_group_mappings = {
        "group1": lambda obj: obj["prop_1"] == "a",
        "group2": lambda obj: obj["prop_1"] == "b",
        "group3": lambda obj: obj["prop_1"] == "c",
    }
    mock_build_unique_val_groups.return_value = mock_group_mappings

    mock_obj_list = [
        {"prop_1": "a", "prop_2": 1},
        {"prop_1": "b", "prop_2": 2},
        {"prop_1": "c", "prop_2": 3},
    ]
    # pylint:disable=protected-access
    res = instance._run_group_by(mock_obj_list)
    mock_build_unique_val_groups.assert_called_once_with(mock_obj_list)

    assert res == {
        "group1": [{"prop_1": "a", "prop_2": 1}],
        "group2": [{"prop_1": "b", "prop_2": 2}],
        "group3": [{"prop_1": "c", "prop_2": 3}],
    }


@patch("openstack_query.query_blocks.query_parser.QueryParser._build_unique_val_groups")
def test_run_group_by_with_group_mappings(mock_build_unique_val_groups, instance):
    """
    Tests run group_by method functions expectedly - when using group mappings
    Should use the preset mappings and apply them onto given object list
    """
    instance.group_by = MockProperties.PROP_1

    mock_group_mappings = {
        "group1": lambda obj: obj["prop_2"] in [1, 2],
        "group2": lambda obj: obj["prop_2"] in [3],
    }
    instance.group_mappings = mock_group_mappings

    mock_obj_list = [
        {"prop_1": "a", "prop_2": 1},
        {"prop_1": "b", "prop_2": 2},
        {"prop_1": "c", "prop_2": 3},
    ]

    # pylint:disable=protected-access
    res = instance._run_group_by(mock_obj_list)
    mock_build_unique_val_groups.assert_not_called()

    assert res == {
        "group1": [{"prop_1": "a", "prop_2": 1}, {"prop_1": "b", "prop_2": 2}],
        "group2": [{"prop_1": "c", "prop_2": 3}],
    }


def test_reset(instance):
    """
    Tests reset function resets group_by and sort_by attrs
    """
    instance.reset()
    assert instance.group_by is None
    assert instance.group_mappings == {}
    assert instance.sort_by == {}
