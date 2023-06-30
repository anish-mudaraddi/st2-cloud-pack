import unittest
from parameterized import parameterized

from nose.tools import raises

from openstack_query.handlers.client_side_handler_string import ClientSideHandlerString
from tests.lib.openstack_query.mocks.mocked_props import MockProperties

from enums.query.query_presets import QueryPresetsString
from exceptions.missing_mandatory_param_error import MissingMandatoryParamError


class ClientSideHandlerStringTests(unittest.TestCase):
    """
    Run various tests to ensure that ClientSideHandlerString class methods function expectedly
    """

    def setUp(self):
        """
        Setup for tests
        """
        super().setUp()
        _FILTER_FUNCTION_MAPPINGS = {
            preset: [MockProperties.PROP_1] for preset in QueryPresetsString
        }
        self.instance = ClientSideHandlerString(_FILTER_FUNCTION_MAPPINGS)

    @parameterized.expand(
        [(f"test {preset.name}", preset) for preset in QueryPresetsString]
    )
    def test_check_supported_all_presets(self, name, preset):
        """
        Tests that handler supports all generic query client_side
        """
        self.assertTrue(self.instance.check_supported(preset, MockProperties.PROP_1))

    @parameterized.expand(
        [
            ("Numeric digits only", "[0-9]+", "123", True),
            ("Alphabetic characters only", "[A-Za-z]+", "abc", True),
            ("No alphabetic characters", "[A-Za-z]+", "123", False),
            ("Alphabetic and numeric characters", "[A-Za-z0-9]+", "abc123", True),
            ("Empty string, no match", "[A-Za-z]+", "", False),
        ]
    )
    def test_prop_matches_regex_valid(
        self, name, regex_string, test_prop, expected_out
    ):
        out = self.instance._prop_matches_regex(test_prop, regex_string)
        assert out == expected_out

    @parameterized.expand(
        [
            ("item is in", ["val1", "val2", "val3"], "val1", True),
            ("item is not in", ["val1", "val2"], "val3", False),
        ]
    )
    def test_prop_any_in(self, name, val_list, test_prop, expected_out):
        out = self.instance._prop_any_in(test_prop, val_list)
        assert out == expected_out

    @raises(MissingMandatoryParamError)
    def test_prop_any_in_empty_list(self):
        self.instance._prop_any_in("some-prop-val", [])

    @parameterized.expand(
        [
            ("item is in", ["val1", "val2", "val3"], "val1", False),
            ("item is not in", ["val1", "val2"], "val3", True),
        ]
    )
    def test_prop_not_any_in(self, name, val_list, test_prop, expected_out):
        out = self.instance._prop_not_any_in(test_prop, val_list)
        assert out == expected_out
