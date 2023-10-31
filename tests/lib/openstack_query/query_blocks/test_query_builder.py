from unittest.mock import MagicMock, patch
import pytest

from openstack_query.query_blocks.query_builder import QueryBuilder

from exceptions.query_preset_mapping_error import QueryPresetMappingError
from exceptions.query_property_mapping_error import QueryPropertyMappingError

from tests.lib.openstack_query.mocks.mocked_query_presets import MockQueryPresets
from tests.lib.openstack_query.mocks.mocked_props import MockProperties


@pytest.fixture(name="mock_client_side_handlers")
def client_side_handlers_fixture():
    """
    Returns a dictionary of mocked client_side_handler objects
    """
    return {"mock_client_handler_1": MagicMock(), "mock_client_handler_2": MagicMock()}


@pytest.fixture(name="mock_server_side_handler")
def server_side_handler_fixture():
    """
    Returns a mocked server_side_handler_object
    """
    return MagicMock()


@pytest.fixture(name="instance")
def instance_fixture(mock_client_side_handlers, mock_server_side_handler):
    """
    Returns an instance with mocked client_side_handlers and
    server_side_handler injects
    """
    mock_prop_enum_cls = MockProperties
    instance = QueryBuilder(
        prop_enum_cls=mock_prop_enum_cls,
        client_side_handlers=list(mock_client_side_handlers.values()),
        server_side_handler=mock_server_side_handler,
    )
    return instance


@pytest.fixture(name="run_parse_where_test_case")
def run_parse_where_test_case_fixture(instance, mock_server_side_handler):
    """
    Fixture to run parse where test cases
    """

    mock_client_side_handler = MagicMock()
    mock_client_filter_func = MagicMock()
    mock_client_side_handler.get_filter_func.return_value = mock_client_filter_func

    def _run_parse_where_test_case(mock_server_side_filters, mock_kwargs):
        """
        run parse where test case where get_filter_func returns different server-side-filters
        """

        mock_server_side_handler.get_filters.return_value = mock_server_side_filters
        with patch(
            "openstack_query.query_blocks.query_builder.QueryBuilder._get_preset_handler"
        ) as mock_get_preset_handler:
            with patch(
                "openstack_query.query_blocks.query_builder.QueryBuilder._add_filter"
            ) as mock_add_filter:
                mock_get_preset_handler.return_value = mock_client_side_handler
                with patch.object(MockProperties, "get_prop_mapping") as mock_prop_func:
                    instance.parse_where(
                        MockQueryPresets.ITEM_1, MockProperties.PROP_1, mock_kwargs
                    )

        mock_get_preset_handler.assert_called_once_with(
            MockQueryPresets.ITEM_1, MockProperties.PROP_1
        )
        mock_client_side_handler.get_filter_func.assert_called_once_with(
            preset=MockQueryPresets.ITEM_1,
            prop=MockProperties.PROP_1,
            prop_func=mock_prop_func.return_value,
            filter_func_kwargs=mock_kwargs,
        )
        mock_server_side_handler.get_filters.assert_called_once_with(
            preset=MockQueryPresets.ITEM_1,
            prop=MockProperties.PROP_1,
            params=mock_kwargs,
        )

        mock_add_filter.assert_called_once_with(
            client_side_filter=mock_client_filter_func,
            server_side_filters=mock_server_side_filters,
        )

    return _run_parse_where_test_case


def test_parse_where_gets_single_filter(run_parse_where_test_case):
    """
    Tests that parse_where functions expectedly
    - where server-side-handler get_filter_func returns a single filter set
    """

    # setup mocks
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}
    run_parse_where_test_case({"filter1": "val1", "filter2": "val2"}, mock_kwargs)


def test_parse_where_gets_multiple_filters(run_parse_where_test_case):
    """
    Tests that parse_where functions expectedly
    - where server-side-handler get_filter_func returns a list of filters
    """

    # setup mocks
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}
    run_parse_where_test_case([{"filter1": "val1"}, {"filter2": "val2"}], mock_kwargs)


def test_parse_where_gets_no_filters(run_parse_where_test_case):
    """
    Tests that parse_where functions expectedly
    - where server-side-handler get_filter_func returns no filter
    """

    # setup mocks
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}
    run_parse_where_test_case(None, mock_kwargs)


def test_parse_where_prop_invalid(instance):
    """
    Tests that parse_where functions expectedly - where inputs invalid
    method raises QueryPropertyMappingError when prop_handler.get_prop_mapping returns None
    """

    # test if prop_mapping doesn't exist
    instance.client_side_filter = None

    with patch.object(MockProperties, "get_prop_mapping") as mock_prop_func:
        mock_prop_func.return_value = None
        with pytest.raises(QueryPropertyMappingError):
            instance.parse_where(MockQueryPresets.ITEM_1, MockProperties.PROP_1)
    mock_prop_func.assert_called_once_with(MockProperties.PROP_1)


def test_get_preset_handler_valid(instance, mock_client_side_handlers):
    """
    Tests that get_preset_handler functions expectedly - where inputs invalid
    method should return a client_handler that supports a given preset-property pair
    """
    mock_client_side_handlers[
        "mock_client_handler_1"
    ].check_supported.return_value = False
    mock_client_side_handlers[
        "mock_client_handler_2"
    ].check_supported.return_value = True

    # pylint:disable=protected-access
    # check when preset found
    res = instance._get_preset_handler(MockQueryPresets.ITEM_1, MockProperties.PROP_1)
    assert res == mock_client_side_handlers["mock_client_handler_2"]


def test_get_preset_handler_invalid_prop(instance, mock_client_side_handlers):
    """
    Tests that get_preset_handler functions expectedly - where preset valid but prop invalid
    method raises QueryPresetMappingError when no client-side handler available has mapping for preset-property pair
    """
    mock_client_side_handlers["mock_client_handler_1"].preset_known.return_value = False
    mock_client_side_handlers["mock_client_handler_2"].preset_known.return_value = True

    mock_client_side_handlers[
        "mock_client_handler_1"
    ].check_supported.return_value = False
    mock_client_side_handlers[
        "mock_client_handler_2"
    ].check_supported.return_value = False

    with pytest.raises(QueryPresetMappingError):
        # pylint:disable=protected-access
        instance._get_preset_handler(MockQueryPresets.ITEM_1, MockProperties.PROP_1)


def test_client_side_filter_none_before(instance):
    """
    Tests client_side_filter property methods
    """
    instance.client_side_filter = ["some-client-side-filter"]
    res = instance.client_side_filter
    assert res == ["some-client-side-filter"]


def test_server_side_filters(instance):
    """
    Tests server_side_filters property methods
    """
    instance.server_side_filters = "some-server-side-filter"
    res = instance.server_side_filters
    assert res == "some-server-side-filter"


def test_server_filter_fallback(instance):
    """
    Tests server_filter_fallback property methods
    """
    instance.server_filter_fallback = "some-client-side-filter"
    res = instance.server_filter_fallback
    assert res == "some-client-side-filter"


def test_add_filter_no_server_side_filter(instance):
    """
    Tests add_filter method works properly - with no server filters
    Should only set client_side_filter
    """
    mock_client_side_filter = MagicMock()

    # pylint:disable=protected-access
    instance._add_filter(
        client_side_filter=mock_client_side_filter, server_side_filters=None
    )
    instance.client_side_filters = [mock_client_side_filter]


@pytest.mark.parametrize(
    "set_server_side_filters, server_side_filters, expected_values",
    [
        # no previous filters set
        # one server-side filter to add
        ([], [{"filter1": "val1"}], [{"filter1": "val1"}]),
        # one (non-overlapping) server-side filter set
        # one server-side filter set to add
        (
            [{"filter1": "val1"}],
            [{"filter2": "val2"}],
            [{"filter1": "val1", "filter2": "val2"}],
        ),
        # multiple (non-overlapping) server-side filters set, one
        # one server-side filter set to add
        (
            [{"filter1": "val1"}, {"filter2": "val2"}],
            [{"filter3": "val3"}],
            [
                {"filter1": "val1", "filter3": "val3"},
                {"filter2": "val2", "filter3": "val3"},
            ],
        ),
        # multiple (non-overlapping) server-side filters set
        # multiple server-side filter sets to add
        (
            [{"filter1": "val1"}, {"filter2": "val2"}],
            [{"filter3": "val3"}, {"filter4": "val4"}],
            [
                {"filter1": "val1", "filter3": "val3"},
                {"filter1": "val1", "filter4": "val4"},
                {"filter2": "val2", "filter3": "val3"},
                {"filter2": "val2", "filter4": "val4"},
            ],
        ),
    ],
)
def test_add_filter_with_server_side_filter(
    set_server_side_filters, server_side_filters, expected_values, instance
):
    """
    Tests add_filter method works properly - with one set of server side filters
    Should only set client_side_filter
    """
    mock_client_side_filter = MagicMock()
    instance.server_side_filters = set_server_side_filters

    # pylint:disable=protected-access
    instance._add_filter(
        client_side_filter=mock_client_side_filter,
        server_side_filters=server_side_filters,
    )

    assert instance.server_side_filters == expected_values
    assert instance.server_filter_fallback == [mock_client_side_filter]


def test_add_filter_conflicting_presets(instance):
    """
    Tests add_filter method works properly - when a conflict occurs between
    server-side filter params - add new server-side filter as client-side filter
    """
    instance.client_side_filters = []
    instance.server_side_filters = [{"filter1": "val1"}]

    # pylint:disable=protected-access
    instance._add_filter(
        client_side_filter="client-side-filter",
        server_side_filters=[{"filter1": "val2"}],
    )

    assert instance.server_side_filters == [{"filter1": "val1"}]
    assert instance.client_side_filters == ["client-side-filter"]


def test_reset(instance):
    """
    Tests reset function resets client and server filters
    """
    instance.reset()
    assert instance.client_side_filters == []
    assert instance.server_side_filters == []
    assert instance.server_filter_fallback == []
