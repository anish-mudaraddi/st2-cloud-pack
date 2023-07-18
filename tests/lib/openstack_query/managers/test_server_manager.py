import unittest
from unittest.mock import MagicMock, patch, NonCallableMock

from openstack_query.managers.server_manager import ServerManager

from enums.query.query_presets import (
    QueryPresetsDateTime,
    QueryPresetsString,
    QueryPresetsGeneric,
)
from enums.query.props.server_properties import ServerProperties
from enums.query.query_output_types import QueryOutputTypes
from structs.query.query_preset_details import QueryPresetDetails


@patch("openstack_query.managers.query_manager.QueryManager._build_and_run_query")
@patch("openstack_query.managers.server_manager.QueryOutputDetails")
class ServerManagerTests(unittest.TestCase):
    """
    Runs various tests to ensure that ServerManager class methods function expectedly
    """

    def setUp(self) -> None:
        """
        Setup for tests
        """
        super().setUp()

        self.query = MagicMock()
        self.instance = ServerManager(cloud_account="test_account")

        # pylint:disable=protected-access
        self.instance._query = self.query

    def test_search_all(self, mock_query_output_details, mock_build_and_run_query):
        """
        Tests that search_all method functions expectedly
        Runs a query to get all servers, returns query results
        """
        mock_query_return = NonCallableMock()
        mock_build_and_run_query.return_value = mock_query_return

        mock_output_details = MagicMock()
        mock_query_output_details.from_kwargs.return_value = mock_output_details

        mock_kwargs = {
            "properties_to_select": ["server_name", "server_id"],
            "output_type": QueryOutputTypes.TO_STR,
        }

        res = self.instance.search_all(**mock_kwargs)
        mock_build_and_run_query.assert_called_once_with(
            preset_details=None, output_details=mock_output_details
        )

        self.assertEqual(res, mock_query_return)

    def test_search_by_datetime(
        self, mock_query_output_details, mock_build_and_run_query
    ):
        """
        Tests that search_by_datetime method functions expectedly
        Run a datetime query - in this case get all servers older than a relative time
        """
        mock_query_return = NonCallableMock()
        mock_build_and_run_query.return_value = mock_query_return

        mock_output_details = MagicMock()
        mock_query_output_details.from_kwargs.return_value = mock_output_details

        mock_kwargs = {
            "properties_to_select": ["server_name", "server_id"],
            "output_type": QueryOutputTypes.TO_STR,
        }

        res = self.instance.search_by_datetime(
            search_mode="older_than",
            property_to_search_by="server_creation_date",
            days=10,
            hours=10,
            minutes=1,
            **mock_kwargs
        )

        mock_build_and_run_query.assert_called_once_with(
            preset_details=QueryPresetDetails(
                preset=QueryPresetsDateTime.OLDER_THAN,
                prop=ServerProperties.SERVER_CREATION_DATE,
                args={
                    "days": 10,
                    "hours": 10,
                    "minutes": 1,
                    "seconds": 0,
                },
            ),
            output_details=mock_output_details,
        )
        self.assertEqual(res, mock_query_return)

    def test_search_by_property_with_single_value(
        self, mock_query_output_details, mock_build_and_run_query
    ):
        """
        Tests that search_by_property method functions expectedly - with single value list
        Runs a property query - in this case get servers with matching image_id
        Should build and run a query using EQUAL_TO preset
        """
        mock_query_return = NonCallableMock()
        mock_build_and_run_query.return_value = mock_query_return

        mock_output_details = MagicMock()
        mock_query_output_details.from_kwargs.return_value = mock_output_details

        mock_kwargs = {
            "properties_to_select": ["server_name", "server_id"],
            "output_type": QueryOutputTypes.TO_STR,
        }

        res = self.instance.search_by_property(
            search_mode="any_in",
            property_to_search_by="image_id",
            values=["image-id1"],
            **mock_kwargs
        )

        # should call build with EQUAL_TO and args with keyword value instead
        mock_build_and_run_query.assert_called_once_with(
            preset_details=QueryPresetDetails(
                preset=QueryPresetsGeneric.EQUAL_TO,
                prop=ServerProperties.IMAGE_ID,
                args={"value": "image-id1"},
            ),
            output_details=mock_output_details,
        )
        self.assertEqual(res, mock_query_return)

    def test_search_by_property_with_multiple_values(
        self, mock_query_output_details, mock_build_and_run_query
    ):
        """
        Tests that search_by_property method functions expectedly - with single value list
        Runs a property query - in this case get servers with matching image_id
        """
        mock_query_return = NonCallableMock()
        mock_build_and_run_query.return_value = mock_query_return

        mock_output_details = MagicMock()
        mock_query_output_details.from_kwargs.return_value = mock_output_details

        mock_kwargs = {
            "properties_to_select": ["server_name", "server_id"],
            "output_type": QueryOutputTypes.TO_STR,
        }

        res = self.instance.search_by_property(
            search_mode="any_in",
            property_to_search_by="image_id",
            values=["image-id1", "image-id2"],
            **mock_kwargs
        )

        mock_build_and_run_query.assert_called_once_with(
            preset_details=QueryPresetDetails(
                preset=QueryPresetsString.ANY_IN,
                prop=ServerProperties.IMAGE_ID,
                args={"values": ["image-id1", "image-id2"]},
            ),
            output_details=mock_output_details,
        )
        self.assertEqual(res, mock_query_return)

    @patch("openstack_query.managers.server_manager.re")
    def test_search_by_regex_valid(
        self, mock_re, mock_query_output_details, mock_build_and_run_query
    ):
        """
        Tests that search_by_regex method functions expectedly - with single regex pattern
        Runs a regex pattern query - in this case gets servers with matching pattern on name
        """
        mock_query_return = NonCallableMock()
        mock_build_and_run_query.return_value = mock_query_return

        mock_re_return = NonCallableMock()
        mock_re.compile.return_value = mock_re_return

        mock_output_details = MagicMock()
        mock_query_output_details.from_kwargs.return_value = mock_output_details

        mock_kwargs = {
            "properties_to_select": ["server_name", "server_id"],
            "output_type": QueryOutputTypes.TO_STR,
        }

        res = self.instance.search_by_regex(
            property_to_search_by="server_name",
            pattern="some-regex-pattern",
            **mock_kwargs
        )

        mock_build_and_run_query.assert_called_once_with(
            preset_details=QueryPresetDetails(
                preset=QueryPresetsString.MATCHES_REGEX,
                prop=ServerProperties.SERVER_NAME,
                args={"regex_string": mock_re_return},
            ),
            output_details=mock_output_details,
        )

        self.assertEqual(res, mock_query_return)
