from typing import Callable, Dict
from unittest.mock import ANY, create_autospec, NonCallableMock
from email_api.email_api import EmailApi
from openstack_api.openstack_floating_ip import OpenstackFloatingIP
from openstack_api.openstack_image import OpenstackImage

from openstack_api.openstack_server import OpenstackServer
from openstack_api.openstack_query import OpenstackQuery
from src.email_actions import EmailActions, _EmailActionParams
from nose.tools import raises

from tests.actions.openstack_action_test_base import OpenstackActionTestBase


class TestServerActions(OpenstackActionTestBase):
    """
    Unit tests for the Email.* actions
    """

    action_cls = EmailActions

    def _create_search_api_mock(self, spec):
        # Want to keep mock of __getitem__ otherwise all f"search_{query_preset}"
        # calls will go to the same mock
        mock = create_autospec(spec)
        mock.__getitem__ = spec.__getitem__
        return mock

    # pylint: disable=invalid-name
    def setUp(self):
        """
        Prepares the mock API and injects it into a new instance
        """
        super().setUp()
        self.email_mock = create_autospec(EmailApi)
        self.server_mock = self._create_search_api_mock(OpenstackServer)
        self.floating_ip_mock = self._create_search_api_mock(OpenstackFloatingIP)
        self.image_mock = self._create_search_api_mock(OpenstackImage)

        self.query_mock = create_autospec(OpenstackQuery)

        self.action: EmailActions = self.get_action_instance(
            api_mocks={
                "email_api": self.email_mock,
                "openstack_server_api": self.server_mock,
                "openstack_floating_ip_api": self.floating_ip_mock,
                "openstack_image_api": self.image_mock,
                "openstack_query_api": self.query_mock,
            },
        )

    def test_send_email(self):
        """
        Tests the action that sends an email
        """
        self.action.send_email(
            subject=NonCallableMock(),
            email_to=NonCallableMock(),
            email_from=NonCallableMock(),
            email_cc=NonCallableMock(),
            header=NonCallableMock(),
            footer=NonCallableMock(),
            body=NonCallableMock(),
            attachment_filepaths=NonCallableMock(),
            smtp_account=NonCallableMock(),
            send_as_html=NonCallableMock(),
        )
        self.email_mock.send_email.assert_called_once()

    def _test_email_users(
        self,
        arguments: Dict,
        action_function: Callable,
        action_params: _EmailActionParams,
    ):
        """
        Helper function that checks an email_users action works correctly
        """
        action_function(**arguments)
        action_params.search_api[
            f"search_{arguments['query_preset']}"
        ].assert_called_once_with(
            arguments["cloud_account"],
            arguments["project_identifier"],
            days=arguments["days"],
            ids=arguments["ids"],
            names=arguments["names"],
            name_snippets=arguments["name_snippets"],
        )
        self.query_mock.parse_and_output_table.assert_called_once_with(
            cloud_account=arguments["cloud_account"],
            items=action_params.search_api[
                f"search_{arguments['query_preset']}"
            ].return_value,
            object_type=action_params.object_type,
            properties_to_select=arguments["properties_to_select"],
            group_by=action_params.required_email_property,
            get_html=arguments["send_as_html"],
        )
        self.email_mock.send_emails.assert_called_once_with(
            smtp_accounts=ANY,
            emails=ANY,
            subject=arguments["subject"],
            email_from=arguments["email_from"],
            email_cc=arguments["email_cc"],
            header=arguments["header"],
            footer=arguments["footer"],
            attachment_filepaths=arguments["attachment_filepaths"],
            smtp_account=arguments["smtp_account"],
            test_override=arguments["test_override"],
            test_override_email=arguments["test_override_email"],
            send_as_html=arguments["send_as_html"],
        )

    def test_email_server_users(self):
        """
        Tests the action that sends emails to server users works correctly
        """
        arguments = {
            "cloud_account": "test_account",
            "project_identifier": "test_project",
            "query_preset": "servers_older_than",
            "message": "Message",
            "properties_to_select": ["id", "user_email"],
            "subject": "Subject",
            "email_from": "testemail",
            "email_cc": [],
            "header": "",
            "footer": "",
            "attachment_filepaths": [],
            "smtp_account": "",
            "test_override": False,
            "test_override_email": [""],
            "send_as_html": False,
            "days": 60,
            "ids": None,
            "names": None,
            "name_snippets": None,
        }
        action_params = _EmailActionParams(
            required_email_property="user_email",
            valid_search_queries_no_project=OpenstackServer.SEARCH_QUERY_PRESETS_NO_PROJECT,
            search_api=self.server_mock,
            object_type="server",
        )
        self._test_email_users(arguments, self.action.email_server_users, action_params)

    @raises(ValueError)
    def test_email_server_users_no_email_error(self):
        """
        Tests the action that sends emails to server users gives a value error when user_email
        is not present in the `properties_to_select`
        """
        self.action.email_server_users(
            cloud_account="test_account",
            project_identifier="",
            query_preset="servers_older_than",
            message="Message",
            properties_to_select=["id"],
            subject="Subject",
            email_from="testemail",
            email_cc=[],
            header="",
            footer="",
            attachment_filepaths=[],
            smtp_account="",
            test_override=False,
            test_override_email=[""],
            send_as_html=False,
            days=60,
            ids=None,
            names=None,
            name_snippets=None,
        )

    def _email_server_users(self, query_preset: str):
        """
        Helper for checking email_server_users works correctly
        """
        return self.action.email_server_users(
            cloud_account="test_account",
            project_identifier="",
            query_preset=query_preset,
            message="Message",
            properties_to_select=["user_email"],
            subject="Subject",
            email_from="testemail",
            email_cc=[],
            header="",
            footer="",
            attachment_filepaths=[],
            smtp_account="",
            test_override=False,
            test_override_email=[""],
            send_as_html=False,
            days=60,
            ids=None,
            names=None,
            name_snippets=None,
        )

    def test_email_server_users_no_project(self):
        """
        Tests the action that sends emails to server users does not give a value error when a project
        is required for the query type
        """

        i = 0
        for query_preset in OpenstackServer.SEARCH_QUERY_PRESETS_NO_PROJECT:
            self._email_server_users(query_preset)
            i += 1
            self.assertEqual(self.email_mock.send_emails.call_count, i)

    @raises(ValueError)
    def _check_email_server_users_raises(self, query_preset):
        """
        Helper for checking email_server_users raises a ValueError when needed
        (needed to allow multiple to be checked in the same test otherwise it stops
         after the first error)
        """
        self.assertRaises(ValueError, self._email_server_users(query_preset))

    def test_email_server_users_no_project_error(self):
        """
        Tests the action that sends emails to server users gives a value error when a project is
        required for the query type
        """

        # Should raise an error for all but servers_older_than and servers_last_updated_before
        should_pass = OpenstackServer.SEARCH_QUERY_PRESETS_NO_PROJECT
        should_not_pass = OpenstackServer.SEARCH_QUERY_PRESETS
        for x in should_pass:
            should_not_pass.remove(x)

        for query_preset in should_not_pass:
            self._check_email_server_users_raises(query_preset)

    def test_email_floating_ip_users(self):
        """
        Tests the action that sends emails to floating ip project contacts works correctly
        """
        arguments = {
            "cloud_account": "test_account",
            "project_identifier": "test_project",
            "query_preset": "fips_older_than",
            "message": "Message",
            "properties_to_select": ["id", "project_email"],
            "subject": "Subject",
            "email_from": "testemail",
            "email_cc": [],
            "header": "",
            "footer": "",
            "attachment_filepaths": [],
            "smtp_account": "",
            "test_override": False,
            "test_override_email": [""],
            "send_as_html": False,
            "days": 60,
            "ids": None,
            "names": None,
            "name_snippets": None,
        }
        action_params = _EmailActionParams(
            required_email_property="project_email",
            valid_search_queries_no_project=OpenstackFloatingIP.SEARCH_QUERY_PRESETS_NO_PROJECT,
            search_api=self.floating_ip_mock,
            object_type="floating_ip",
        )
        self._test_email_users(
            arguments, self.action.email_floating_ip_users, action_params
        )

    @raises(ValueError)
    def test_email_floating_ip_users_no_email_error(self):
        """
        Tests the action that sends emails to floating ip users gives a value error when project_email
        is not present in the `properties_to_select`
        """
        self.action.email_floating_ip_users(
            cloud_account="test_account",
            project_identifier="",
            query_preset="fips_older_than",
            message="Message",
            properties_to_select=["id"],
            subject="Subject",
            email_from="testemail",
            email_cc=[],
            header="",
            footer="",
            attachment_filepaths=[],
            smtp_account="",
            test_override=False,
            test_override_email=[""],
            send_as_html=False,
            days=60,
            ids=None,
            names=None,
            name_snippets=None,
        )

    def _email_floating_ip_users(self, query_preset: str):
        """
        Helper for checking email_floating_ip_users works correctly
        """
        return self.action.email_floating_ip_users(
            cloud_account="test_account",
            project_identifier="",
            query_preset=query_preset,
            message="Message",
            properties_to_select=["project_email"],
            subject="Subject",
            email_from="testemail",
            email_cc=[],
            header="",
            footer="",
            attachment_filepaths=[],
            smtp_account="",
            test_override=False,
            test_override_email=[""],
            send_as_html=False,
            days=60,
            ids=None,
            names=None,
            name_snippets=None,
        )

    def test_email_floating_ip_users_no_project(self):
        """
        Tests the action that sends emails to floating ip users does not give a value error when a project
        is required for the query type
        """

        i = 0
        for query_preset in OpenstackFloatingIP.SEARCH_QUERY_PRESETS_NO_PROJECT:
            self._email_floating_ip_users(query_preset)
            i += 1
            self.assertEqual(self.email_mock.send_emails.call_count, i)

    @raises(ValueError)
    def _check_email_floating_ip_users_raises(self, query_preset):
        """
        Helper for checking email_floating_ip_users raises a ValueError when needed
        (needed to allow multiple to be checked in the same test otherwise it stops
         after the first error)
        """
        self.assertRaises(ValueError, self._email_floating_ip_users(query_preset))

    def test_email_floating_ip_users_no_project_error(self):
        """
        Tests the action that sends emails to floating ip users gives a value error when a project
        is required for the query type
        """

        # Should raise an error for all but a few queries
        should_pass = OpenstackFloatingIP.SEARCH_QUERY_PRESETS_NO_PROJECT
        should_not_pass = OpenstackFloatingIP.SEARCH_QUERY_PRESETS
        for x in should_pass:
            should_not_pass.remove(x)

        for query_preset in should_not_pass:
            self._check_email_floating_ip_users_raises(query_preset)

    def test_email_image_users(self):
        """
        Tests the action that sends emails to image project contacts works correctly
        """
        arguments = {
            "cloud_account": "test_account",
            "project_identifier": "test_project",
            "query_preset": "images_older_than",
            "message": "Message",
            "properties_to_select": ["id", "project_email"],
            "subject": "Subject",
            "email_from": "testemail",
            "email_cc": [],
            "header": "",
            "footer": "",
            "attachment_filepaths": [],
            "smtp_account": "",
            "test_override": False,
            "test_override_email": [""],
            "send_as_html": False,
            "days": 60,
            "ids": None,
            "names": None,
            "name_snippets": None,
        }
        action_params = _EmailActionParams(
            required_email_property="project_email",
            valid_search_queries_no_project=OpenstackImage.SEARCH_QUERY_PRESETS_NO_PROJECT,
            search_api=self.image_mock,
            object_type="image",
        )
        self._test_email_users(arguments, self.action.email_image_users, action_params)

    @raises(ValueError)
    def test_email_image_users_no_email_error(self):
        """
        Tests the action that sends emails to image users gives a value error when project_email
        is not present in the `properties_to_select`
        """
        self.action.email_image_users(
            cloud_account="test_account",
            project_identifier="",
            query_preset="images_older_than",
            message="Message",
            properties_to_select=["id"],
            subject="Subject",
            email_from="testemail",
            email_cc=[],
            header="",
            footer="",
            attachment_filepaths=[],
            smtp_account="",
            test_override=False,
            test_override_email=[""],
            send_as_html=False,
            days=60,
            ids=None,
            names=None,
            name_snippets=None,
        )

    def _email_image_users(self, query_preset: str):
        """
        Helper for checking email_image_users works correctly
        """
        return self.action.email_image_users(
            cloud_account="test_account",
            project_identifier="",
            query_preset=query_preset,
            message="Message",
            properties_to_select=["project_email"],
            subject="Subject",
            email_from="testemail",
            email_cc=[],
            header="",
            footer="",
            attachment_filepaths=[],
            smtp_account="",
            test_override=False,
            test_override_email=[""],
            send_as_html=False,
            days=60,
            ids=None,
            names=None,
            name_snippets=None,
        )

    def test_email_image_users_no_project(self):
        """
        Tests the action that sends emails to image users does not give a value error when a project
        is required for the query type
        """

        for i, query_preset in enumerate(
            OpenstackImage.SEARCH_QUERY_PRESETS_NO_PROJECT, start=1
        ):
            self._email_image_users(query_preset)
            self.assertEqual(self.email_mock.send_emails.call_count, i)

    @raises(ValueError)
    def _check_email_image_users_raises(self, query_preset):
        """
        Helper for checking email_image_users raises a ValueError when needed
        (needed to allow multiple to be checked in the same test otherwise it stops
         after the first error)
        """
        self.assertRaises(ValueError, self._email_image_users(query_preset))

    def test_email_image_users_no_project_error(self):
        """
        Tests the action that sends emails to image users gives a value error when a project
        is required for the query type
        """

        # Should raise an error for all but a few queries
        should_pass = OpenstackImage.SEARCH_QUERY_PRESETS_NO_PROJECT
        should_not_pass = OpenstackImage.SEARCH_QUERY_PRESETS
        for x in should_pass:
            should_not_pass.remove(x)

        for query_preset in should_not_pass:
            self._check_email_image_users_raises(query_preset)

    def test_run_method(self):
        """
        Tests that run can dispatch to the Stackstorm facing methods
        """
        expected_methods = [
            "send_email",
            "email_server_users",
            "email_floating_ip_users",
            "email_image_users",
        ]
        self._test_run_dynamic_dispatch(expected_methods)
