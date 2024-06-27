from unittest.mock import MagicMock, patch, call, NonCallableMock

import pytest

from enums.query.query_presets import QueryPresetsGeneric
from exceptions.query_chaining_error import QueryChainingError
from openstack_query.query_blocks.query_chainer import QueryChainer
from tests.lib.openstack_query.mocks.mocked_props import MockProperties


@pytest.fixture(name="instance")
def instance_fixture():
    """
    Returns an instance of QueryChainer with mocked chain mappings
    """

    # sets mock chain mappings
    # mocks MockProperties PROP_1 to PROP_2 - contrived example since
    # the properties should belong to 2 different Queries to be useful
    # - but this is just a test
    _chain_mappings = {MockProperties.PROP_1: MockProperties.PROP_2}
    return QueryChainer(_chain_mappings)


@pytest.fixture(name="run_parse_then_query_valid")
def run_parse_then_query_valid_fixture(instance):
    """
    Fixture that runs a then_query() method test case
    """

    @patch("openstack_query.query_factory.QueryFactory")
    @patch("openstack_query.api.query_api.QueryAPI")
    @patch("openstack_query.query_blocks.query_chainer.QueryTypes")
    def _run_parse_then_query_valid(
        mock_keep_previous_results,
        mock_query_types_cls,
        mock_query_api,
        mock_query_factory,
    ):
        """
        runs a then_query() test case with keep_previous_results being either True or False
        """
        mock_current_query = MagicMock()
        # setting what link props we get
        mock_current_query.chainer.get_link_props.return_value = (
            MockProperties.PROP_1,
            MockProperties.PROP_2,
        )

        # setting prop_values to configure where()
        mock_current_query.select.return_value.to_props.return_value = {
            "prop_1": ["val1", "val2", "val3"]
        }

        res = instance.parse_then(
            current_query=mock_current_query,
            query_type="query-type",
            keep_previous_results=mock_keep_previous_results,
        )

        mock_query_types_cls.from_string.assert_called_once_with("query-type")
        mock_current_query.to_props.assert_called_once()

        # test getting link prop values works
        mock_current_query.select.assert_any_call([MockProperties.PROP_1])
        mock_current_query.select.return_value.to_props.assert_any_call(flatten=True)

        if mock_keep_previous_results:
            mock_query_api.return_value.chainer.set_forwarded_vals.assert_called_once_with(
                MockProperties.PROP_2,
                mock_current_query.group_by.return_value.to_props.return_value,
            )
            mock_group_by = mock_current_query.group_by
            mock_group_by.assert_has_calls(
                [
                    call(MockProperties.PROP_1),
                    call().to_props(),
                ]
            )

        mock_query_factory.build_query_deps.assert_called_once_with(
            mock_query_types_cls.from_string.return_value.value
        )

        mock_query_api.assert_called_once_with(
            mock_query_factory.build_query_deps.return_value
        )

        mock_query_api.return_value.where.assert_called_once_with(
            QueryPresetsGeneric.ANY_IN,
            MockProperties.PROP_2,
            values=["val1", "val2", "val3"],
        )
        assert res == mock_query_api.return_value.where.return_value

    return _run_parse_then_query_valid


def test_forwarded_info(instance):
    """
    Tests forwarded info property outputs a tuple of link_prop and
    forwarded_values attributes. Uses set_forwarded_vals to set the properties
    """
    mock_forwarded_values = NonCallableMock()
    mock_link_prop = NonCallableMock()
    instance.set_forwarded_vals(mock_link_prop, mock_forwarded_values)
    assert instance.forwarded_info == (mock_link_prop, mock_forwarded_values)


def test_get_chaining_props(instance):
    """
    Tests that get_chaining_props method works as expected
    should return a list of chain_mapping keys
    """
    assert instance.get_chaining_props() == [MockProperties.PROP_1]


def test_check_prop_supported_valid(instance):
    """
    Tests check_prop_supported method - with a valid property
    should return True since property is key in chain_mappings
    """
    assert instance.check_prop_supported(MockProperties.PROP_1)


def test_check_prop_supported_invalid(instance):
    """
    Tests check_prop_supported method - with an invalid property
    should return False since property is not a key in chain_mappings
    """
    assert not instance.check_prop_supported(MockProperties.PROP_2)


def test_get_link_props_valid_query(instance):
    """
    Tests get_link_props method - with valid query - which has a chain mapping
    should return link props
    """
    # a set of mock_properties that the input query returns
    mock_props = [MockProperties.PROP_2, MockProperties.PROP_3]

    mock_query = MagicMock()
    mock_query.value.get_prop_mapping.return_value = mock_props

    mock_link_props = instance.get_link_props(mock_query)
    assert mock_link_props[0] == MockProperties.PROP_1
    assert mock_link_props[1] == MockProperties.PROP_2


def test_get_link_props_no_mapping(instance):
    """
    Tests get_link_props method - with invalid query chain mappings
    should return none
    """
    mock_props = [MockProperties.PROP_3, MockProperties.PROP_4]

    mock_query = MagicMock()
    mock_query.value.get_prop_mapping.return_value = mock_props

    assert instance.get_link_props(mock_query) is None


def test_parse_then_query_valid_no_forward(run_parse_then_query_valid):
    """
    Tests parse_then method - with valid params
    should run parse_then with keep_previous_results = False
    """
    run_parse_then_query_valid(False)


def test_parse_then_query_valid_with_forward(run_parse_then_query_valid):
    """
    Tests parse_then method - with valid params
    should run parse_then with forward outputs = True
    """
    run_parse_then_query_valid(True)


def test_parse_then_no_link_props(instance):
    """
    Tests parse_then method - where no link props available
    should raise error
    """
    mock_current_query = MagicMock()
    mock_current_query.chainer.get_link_props.return_value = None

    mock_query_type = MagicMock()

    with pytest.raises(QueryChainingError):
        instance.parse_then(
            current_query=mock_current_query,
            query_type=mock_query_type,
            keep_previous_results=False,
        )
        mock_current_query.chainer.get_link_props.assert_called_once_with(
            mock_query_type
        )


def test_parse_then_no_results(instance):
    """
    Tests parse_then method - where no results found
    should raise error
    """
    mock_current_query = MagicMock()
    mock_current_query.chainer.get_link_props.return_value = (
        "current-prop",
        "new-prop",
    )
    mock_current_query.to_props.return_value = None
    mock_query_type = MagicMock()

    with pytest.raises(QueryChainingError):
        instance.parse_then(
            current_query=mock_current_query,
            query_type=mock_query_type,
            keep_previous_results=False,
        )
    mock_current_query.chainer.get_link_props.assert_called_once_with(mock_query_type)
    mock_current_query.to_props.assert_called_once()


@patch("openstack_query.query_blocks.query_chainer.QueryTypes")
def test_run_append_from_query(mock_query_types, instance):
    """
    tests run_append_from_query method - calls then() to get a new query and runs it, selecting
    given props and return grouped values
    """
    mock_current_query = NonCallableMock()
    mock_cloud_account = NonCallableMock()
    query_type = "query_type"
    mock_props = ["prop1", "prop2"]

    mock_current_query.chainer.get_link_props.return_value = (
        "current_link_prop",
        "new_link_prop",
    )
    mock_new_query = mock_current_query.then.return_value

    res = instance.run_append_from_query(
        mock_current_query, query_type, mock_cloud_account, mock_props
    )

    mock_query_types.from_string.assert_called_once_with(query_type)
    mock_current_query.then.assert_called_once_with(
        mock_query_types.from_string.return_value, keep_previous_results=False
    )
    mock_new_query.select.assert_called_once_with(mock_props)
    mock_new_query.run.assert_called_once_with(mock_cloud_account)
    mock_current_query.chainer.get_link_props.assert_called_once_with(
        mock_query_types.from_string.return_value
    )
    assert res == (
        "current_link_prop",
        mock_new_query.group_by.return_value.to_props.return_value,
    )
