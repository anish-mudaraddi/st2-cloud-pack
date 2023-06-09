import unittest
from unittest.mock import MagicMock, patch
from parameterized import parameterized

from nose.tools import raises

from openstack_query.preset_handlers.preset_handler_string import PresetHandlerString
from enums.query.query_presets import QueryPresetsString
from exceptions.missing_mandatory_param_error import MissingMandatoryParamError


class PresetHandlerGenericTests(unittest.TestCase):
    """
    Run various tests to ensure that PresetHandlerGeneric class methods function expectedly
    """

    def setUp(self):
        """
        Setup for tests
        """
        super().setUp()
        self.instance = PresetHandlerString()

    @parameterized.expand(
        [(f"test {preset.name}", preset) for preset in QueryPresetsString]
    )
    def test_check_preset_supported_all_presets(self, name, preset):
        """
        Tests that handler supports all generic query presets
        """
        self.assertTrue(self.instance.check_preset_supported(preset))

    @parameterized.expand(
        [(f"test {preset.name}", preset) for preset in QueryPresetsString]
    )
    def test_get_mapping_all_presets(self, name, preset):
        """
        Tests that handler supports all generic query presets
        """
        self.assertIsNotNone(self.instance._get_mapping(preset))

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
