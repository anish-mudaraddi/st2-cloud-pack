from dataclasses import dataclass
import datetime
import unittest
from unittest import mock
from unittest.mock import MagicMock, patch, NonCallableMock, Mock
from parameterized import parameterized

from nose.tools import raises, assert_raises
import openstack

from openstack.exceptions import HttpException
from exceptions.item_not_found_error import ItemNotFoundError
from exceptions.missing_mandatory_param_error import MissingMandatoryParamError

from openstack_api.openstack_server import OpenstackServer
from openstack_api.openstack_image import OpenstackImage
from openstack_api.openstack_flavor import OpenstackFlavor

from tests.lib.test_openstack_query_email_base import OpenstackQueryEmailBaseTests


# pylint:disable=too-many-public-methods
class OpenstackServerTests(unittest.TestCase, OpenstackQueryEmailBaseTests):
    """
    Runs various tests to ensure we are using the Openstack
    Servers module in the expected way
    """

    def setUp(self) -> None:
        super().setUp()
        self.mocked_connection = MagicMock()
        with patch("openstack_api.openstack_server.OpenstackIdentity") as identity_mock:
            self.instance = OpenstackServer(self.mocked_connection)
            self.search_query_presets = OpenstackServer.SEARCH_QUERY_PRESETS
            self.search_query_presets_no_project = (
                OpenstackServer.SEARCH_QUERY_PRESETS_NO_PROJECT
            )

            self.identity_module = identity_mock.return_value

        self.api = self.mocked_connection.return_value.__enter__.return_value

        self.mock_server_list = [
            {
                "id": "serverid1",
                "name": "server1",
                "created_at": "2020-06-28T14:00:00Z",
                "updated_at": "2020-06-28T14:00:00Z",
                "status": "SHUTOFF",
            },
            {
                "id": "serverid2",
                "name": "server2",
                "created_at": "2021-04-28T14:00:00Z",
                "updated_at": "2021-06-28T14:00:00Z",
                "status": "ERROR",
            },
            {
                "id": "serverid3",
                "name": "server3",
                "created_at": "2021-06-28T14:00:00Z",
                "updated_at": "2021-06-28T14:00:00Z",
                "status": ["SHUTOFF", "ERROR"],
            },
        ]

    def test_property_funcs(self):
        """
        Tests calling get_query_property_funcs
        """

        @dataclass
        class _ServerMock:
            user_id: str

            def __getitem__(self, attr):
                return getattr(self, attr)

        item = _ServerMock("UserID")
        property_funcs = self.instance.get_query_property_funcs("test")

        # Test user_email
        result = property_funcs["user_email"](item)
        self.assertEqual(result, self.api.identity.find_user.return_value["user_email"])

        # Test user_name
        result = property_funcs["user_name"](item)
        self.assertEqual(result, self.api.identity.find_user.return_value["user_name"])

    def test_search_all_servers_no_project(self):
        """
        Tests calling search_all_servers with no project selected
        """

        @dataclass
        class _ProjectMock:
            # pylint: disable=invalid-name
            id: str

        self.identity_module.list_projects.return_value = [
            _ProjectMock("ID1"),
            _ProjectMock("ID2"),
        ]

        self.instance.search_all_servers(cloud_account="test", project_identifier="")

        self.identity_module.list_projects.assert_called_once_with("test")
        self.mocked_connection.assert_called_once_with("test")

        self.api.list_servers.assert_has_calls(
            [
                mock.call(
                    filters={
                        "all_tenants": True,
                        "project_id": "ID1",
                    }
                ),
                mock.call(
                    filters={
                        "all_tenants": True,
                        "project_id": "ID2",
                    }
                ),
            ],
            any_order=True,
        )

    def test_search_all_servers(self):
        """
        Tests calling search_all_servers
        """
        self.instance.search_all_servers(
            cloud_account="test", project_identifier="project"
        )

        self.identity_module.find_mandatory_project.assert_called_once_with(
            "test", project_identifier="project"
        )
        self.mocked_connection.assert_called_once_with("test")

        self.api.list_servers.assert_called_once_with(
            filters={
                "all_tenants": True,
                "project_id": self.identity_module.find_mandatory_project.return_value.id,
            }
        )

    def test_search_all_servers_error(self):
        """
        Tests calling search_all_servers handles a HttpException correctly
        """
        self.api.list_servers.side_effect = HttpException()
        self.instance.search_all_servers(
            cloud_account="test", project_identifier="project"
        )

        self.identity_module.find_mandatory_project.assert_called_once_with(
            "test", project_identifier="project"
        )
        self.mocked_connection.assert_called_once_with("test")

        self.api.list_servers.assert_called_once_with(
            filters={
                "all_tenants": True,
                "project_id": self.identity_module.find_mandatory_project.return_value.id,
            }
        )

    @mock.patch("openstack_api.openstack_query.datetime", wraps=datetime)
    def test_search_servers_older_than(self, mock_datetime):
        """
        Tests calling search_servers_older_than
        """
        mock_datetime.datetime.now.return_value = datetime.datetime(2021, 8, 1)

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_older_than(
            cloud_account="test", project_identifier="", days=60
        )

        self.assertEqual(result, [self.mock_server_list[0], self.mock_server_list[1]])

    @mock.patch("openstack_api.openstack_query.datetime", wraps=datetime)
    def test_search_servers_younger_than(self, mock_datetime):
        """
        Tests calling search_servers_younger_than
        """
        mock_datetime.datetime.now.return_value = datetime.datetime(2021, 8, 1)

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_younger_than(
            cloud_account="test", project_identifier="", days=60
        )

        self.assertEqual(result, [self.mock_server_list[2]])

    @mock.patch("openstack_api.openstack_query.datetime", wraps=datetime)
    def test_search_servers_last_updated_before(self, mock_datetime):
        """
        Tests calling search_servers_last_updated_before
        """
        mock_datetime.datetime.now.return_value = datetime.datetime(2021, 8, 1)

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_last_updated_before(
            cloud_account="test", project_identifier="", days=60
        )

        self.assertEqual(result, [self.mock_server_list[0]])

    @mock.patch("openstack_api.openstack_query.datetime", wraps=datetime)
    def test_search_servers_last_updated_after(self, mock_datetime):
        """
        Tests calling search_servers_last_updated_after
        """
        mock_datetime.datetime.now.return_value = datetime.datetime(2021, 8, 1)

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_last_updated_after(
            cloud_account="test", project_identifier="", days=60
        )

        self.assertEqual(result, [self.mock_server_list[1], self.mock_server_list[2]])

    def test_search_servers_name_in(self):
        """
        Tests calling search_servers_name_in
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_name_in(
            cloud_account="test", project_identifier="", names=["server1", "server2"]
        )

        self.assertEqual(result, [self.mock_server_list[0], self.mock_server_list[1]])

    def test_search_servers_name_not_in(self):
        """
        Tests calling search_servers_name_not_in
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_name_not_in(
            cloud_account="test", project_identifier="", names=["server1", "server2"]
        )

        self.assertEqual(result, [self.mock_server_list[2]])

    def test_search_servers_name_contains(self):
        """
        Tests calling search_servers_name_contains
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_name_contains(
            cloud_account="test", project_identifier="", name_snippets=["server", "1"]
        )

        self.assertEqual(result, [self.mock_server_list[0]])

        result = self.instance.search_servers_name_contains(
            cloud_account="test", project_identifier="", name_snippets=["1"]
        )

        self.assertEqual(result, [self.mock_server_list[0]])

        result = self.instance.search_servers_name_contains(
            cloud_account="test", project_identifier="", name_snippets=["server"]
        )

        self.assertEqual(result, self.mock_server_list)

    def test_search_servers_name_not_contains(self):
        """
        Tests calling search_servers_name_not_contains
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_name_not_contains(
            cloud_account="test", project_identifier="", name_snippets=["server", "1"]
        )

        self.assertEqual(result, [])

        result = self.instance.search_servers_name_not_contains(
            cloud_account="test", project_identifier="", name_snippets=["1"]
        )

        self.assertEqual(result, [self.mock_server_list[1], self.mock_server_list[2]])

        result = self.instance.search_servers_name_not_contains(
            cloud_account="test", project_identifier="", name_snippets=["server"]
        )

        self.assertEqual(result, [])

    def test_search_servers_id_in(self):
        """
        Tests calling search_servers_id_in
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_id_in(
            cloud_account="test", project_identifier="", ids=["serverid1", "serverid2"]
        )

        self.assertEqual(result, [self.mock_server_list[0], self.mock_server_list[1]])

    def test_search_servers_id_not_in(self):
        """
        Tests calling search_servers_id_not_in
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_id_not_in(
            cloud_account="test", project_identifier="", ids=["serverid1", "serverid2"]
        )

        self.assertEqual(result, [self.mock_server_list[2]])

    def test_search_servers_errored(self):
        """
        Tests calling search_servers_errored
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_errored(
            cloud_account="test", project_identifier=""
        )

        self.assertEqual(result, [self.mock_server_list[1], self.mock_server_list[2]])

    def test_search_servers_shutoff(self):
        """
        Tests calling search_servers_errored
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_shutoff(
            cloud_account="test", project_identifier=""
        )

        self.assertEqual(result, [self.mock_server_list[0], self.mock_server_list[2]])

    def test_search_servers_errored_and_shutoff(self):
        """
        Tests calling search_servers_errored_and_shutoff
        """

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_errored_and_shutoff(
            cloud_account="test", project_identifier=""
        )

        self.assertEqual(result, [self.mock_server_list[2]])

    @mock.patch("openstack_api.openstack_query.datetime", wraps=datetime)
    def test_search_servers_shutoff_before(self, mock_datetime):
        """
        Tests calling search_servers_shutoff_before
        """
        mock_datetime.datetime.now.return_value = datetime.datetime(2021, 8, 1)

        self.instance.search_all_servers = MagicMock()
        self.instance.search_all_servers.return_value = self.mock_server_list

        result = self.instance.search_servers_shutoff_before(
            cloud_account="test", project_identifier="", days=60
        )

        self.assertEqual(result, [self.mock_server_list[0]])

    def test_find_non_existent_servers(self):
        """
        Tests calling find_non_existent_servers
        """

        @dataclass
        class _ObjectMock:
            # pylint: disable=invalid-name
            id: str
            project_id: str

            def __getitem__(self, item):
                return getattr(self, item)

        self.api.list_servers.return_value = [
            _ObjectMock("ObjectID1", "ProjectID1"),
            _ObjectMock("ObjectID2", "ProjectID1"),
            _ObjectMock("ObjectID3", "ProjectID1"),
        ]

        self.api.compute.get_server.side_effect = [
            openstack.exceptions.ResourceNotFound(),
            openstack.exceptions.ResourceNotFound(),
            "",
        ]

        result = self.instance.find_non_existent_servers(
            cloud_account="test", project_identifier="project"
        )

        self.assertEqual(
            result,
            {
                self.api.identity.find_project.return_value.id: [
                    "ObjectID1",
                    "ObjectID2",
                ]
            },
        )

    def test_find_non_existent_projects(self):
        """
        Tests calling find_non_existent_projects
        """

        @dataclass
        class _ObjectMock:
            # pylint: disable=invalid-name
            id: str
            project_id: str

            def __getitem__(self, item):
                return getattr(self, item)

        self.api.list_servers.return_value = [
            _ObjectMock("ServerID1", "ProjectID1"),
            _ObjectMock("ServerID2", "ProjectID1"),
            _ObjectMock("ServerID3", "ProjectID2"),
        ]

        self.api.identity.get_project.side_effect = [
            openstack.exceptions.ResourceNotFound(),
            openstack.exceptions.ResourceNotFound(),
            "",
        ]

        result = self.instance.find_non_existent_projects(cloud_account="test")

        self.assertEqual(result, {"ProjectID1": ["ServerID1", "ServerID2"]})

    @raises(MissingMandatoryParamError)
    def test_find_server_raises_for_missing_param(self):
        """
        Tests that find server will raise error if the identifier is missing
        """
        self.instance.find_server(NonCallableMock(), " ")

    def test_find_server_with_found_result(self):
        """
        Tests that find server returns the result as-is
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()
        _ = self.instance.find_server(cloud, identifier)

        self.mocked_connection.assert_called_once_with(cloud)
        self.api.find_network.assert_called_once_with(
            identifier.strip(), ignore_missing=True
        )

    @raises(ItemNotFoundError)
    def test_start_server_not_found(self):
        """
        Tests that start server will raise error if the server not found
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()
        self.instance.find_server = Mock(return_value=None)
        self.instance.start_server(cloud, identifier)

    @raises(RuntimeError)
    def test_start_server_not_active(self):
        """
        Tests that start server will raise error if the server was not SHUTOFF
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()
        self.instance.find_server = Mock(return_value={"status": "ACTIVE"})
        returned = self.instance.start_server(cloud, identifier)

    def test_start_server_success(self):
        """
        Tests that start server forwards the correct args to OpenStack
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()

        self.instance.find_server = Mock(return_value={"status": "SHUTOFF"})
        self.instance._OpenstackServer_wait_for_change = Mock()
        self.instance.start_server(cloud, identifier)

        self.instance.find_server.assert_called_once_with(identifier)
        self.api.start_server.assert_called_once_with(
            self.instance.find_server.return_value
        )
        self.mocked_connection.assert_called_once_with(cloud)
        self.instance._OpenstackServer_wait_for_change.assert_called_once_with(
            self.instance.find_server.return_value, "ACTIVE"
        )

    @raises(ItemNotFoundError)
    def test_stop_server_not_found(self):
        """
        Tests that stop server will raise error if the server not found
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()
        self.instance.find_server = Mock(return_value=None)
        self.instance.shutoff_server(cloud, identifier)

    @raises(RuntimeError)
    def test_stop_server_not_active(self):
        """
        Tests that stop server will raise error if the server was not ACTIVE
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()
        self.instance.find_server = Mock(return_value={"status": "SHUTOFF"})
        returned = self.instance.shutoff_server(cloud, identifier)

    def test_stop_server_success(self):
        """
        Tests that stop server forwards the correct args to OpenStack
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()

        self.instance.find_server = Mock(return_value={"status": "ACTIVE"})
        self.instance._OpenstackServer_wait_for_change = Mock()
        returned = self.instance.shutoff_server(cloud, identifier)

        self.instance.find_server.assert_called_once_with(identifier)
        self.api.stop_server.assert_called_once_with(
            self.instance.find_server.return_value
        )
        self.mocked_connection.assert_called_once_with(cloud)
        self.instance._OpenstackServer_wait_for_change.assert_called_once_with(
            self.instance.find_server.return_value, "SHUTOFF"
        )
        assert returned

    @raises(ItemNotFoundError)
    def test_reboot_server_not_found(self):
        """
        Test that reboot server will raise error if server not found
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()

        self.instance.find_server = Mock(return_value=None)
        self.instance.reboot_server(cloud, identifier)

    @raises(RuntimeError)
    def test_reboot_server_not_active(self):
        """
        Test that reboot server will raise error if the server was not ACTIVE
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()
        self.instance.find_server = Mock(return_value={"status": "SHUTOFF"})
        returned = self.instance.reboot_server(cloud, identifier)

    @parameterized([True, False])
    def test_reboot_server_success_reboot(self, reboot_flag):
        """
        Test that reboot server forwards the correct args to OpenStack
        """
        cloud, identifier = NonCallableMock(), NonCallableMock()
        self.instance.find_server = Mock(return_value={"status": "ACTIVE"})
        self.instance._OpenstackServer_wait_for_change = Mock()
        returned = self.instance.reboot_server(cloud, identifier, hard_reboot_flag=reboot_flag)

        self.instance.find_server.assert_called_once_with(identifier)
        self.api.reboot_server.assert_called_once_with(
            self.instance.find_server.return_value,
            reboot_flag
        )
        self.mocked_connection.assert_called_once_with(cloud)
        self.instance._OpenstackServer_wait_for_change.assert_called_once_with(
            self.instance.find_server.return_value, "ACTIVE"
        )
        assert returned

    def test_create_server_missing_params(self):
        """
        Test that create server will raise error if mandatory params are missing
        """
        for i in ["name", "flavor_identifier", "image_identifier"]:
            mocked_server_details = NonCallableMock()
            setattr(mocked_server_details, i, "  \t")
            with assert_raises(MissingMandatoryParamError) as e:
                self.instance.create_server(mocked_server_details, NonCallableMock())

        with assert_raises(MissingMandatoryParamError) as e:
            self.instance.create_server(mocked_server_details, "   \t")
