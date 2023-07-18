import unittest
from unittest.mock import patch, NonCallableMock
from parameterized import parameterized

from nose.tools import raises

from openstack_query.handlers.client_side_handler_string import ClientSideHandlerString

from enums.query.query_presets import QueryPresetsString
from exceptions.missing_mandatory_param_error import MissingMandatoryParamError

from tests.lib.openstack_query.mocks.mocked_props import MockProperties

# pylint:disable=protected-access


class ClientSideHandlerStringTests(unittest.TestCase):
    """
    Run various tests to ensure that ClientSideHandlerString class methods function expectedly
    """

    def setUp(self):
        """
        Setup for tests
        """
        super().setUp()
        _filter_function_mappings = {
            preset: [MockProperties.PROP_1] for preset in QueryPresetsString
        }
        self.instance = ClientSideHandlerString(_filter_function_mappings)

    @parameterized.expand(
        [(f"test {preset.name}", preset) for preset in QueryPresetsString]
    )
    def test_check_supported_all_presets(self, _, preset):
        """
        Tests that client_side_handler_string supports all string QueryPresets
        """
        self.assertTrue(self.instance.check_supported(preset, MockProperties.PROP_1))

    @parameterized.expand(
        [
            ("Numeric digits only", "[0-9]+", "123"),
            ("Alphabetic characters only", "[A-Za-z]+", "abc"),
            ("No alphabetic characters", "[A-Za-z]+", "123"),
            ("Alphabetic and numeric characters", "[A-Za-z0-9]+", "abc123"),
            ("Empty string, no match", "[A-Za-z]+", ""),
        ]
    )
    @patch("re.match")
    def test_prop_matches_regex_valid(
        self, _, regex_string, test_prop, mock_regex_match
    ):
        """
        Tests that method prop_matches_regex functions expectedly - with valid regex patterns
        Returns True if test_prop matches given regex pattern regex_string
        """
        mock_regex_match.return_value = test_prop
        self.instance._prop_matches_regex(test_prop, regex_string)
        mock_regex_match.assert_called_once_with(regex_string, test_prop)

    @parameterized.expand(
        [
            ("item is in", ["val1", "val2", "val3"], "val1", True),
            ("item is not in", ["val1", "val2"], "val3", False),
        ]
    )
    def test_prop_any_in(self, _, val_list, test_prop, expected_out):
        """
        Tests that method prop_any_in functions expectedly
        Returns True if test_prop matches any values in a given list val_list
        """
        out = self.instance._prop_any_in(test_prop, val_list)
        assert out == expected_out

    @raises(MissingMandatoryParamError)
    def test_prop_any_in_empty_list(self):
        """
        Tests that method prop_any_in functions expectedly - when given empty list raise error
        """
        self.instance._prop_any_in("some-prop-val", [])

    @parameterized.expand(
        [
            ("item is in", ["val1", "val2", "val3"], "val1", False),
            ("item is not in", ["val1", "val2"], "val3", True),
        ]
    )
    def test_prop_not_any_in(self, _, val_list, test_prop, expected_out):
        """
        Tests that method prop_any_not_in functions expectedly
        Returns True if test_prop does not match any values in a given list val_list
        """
        out = self.instance._prop_not_any_in(test_prop, val_list)
        assert out == expected_out
