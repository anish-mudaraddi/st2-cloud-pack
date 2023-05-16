from typing import List, Dict, Callable, Any, Optional

from openstack.compute.v2.server import Server
from openstack.exceptions import HttpException, ItemNotFoundError, ResourceTimeout
from openstack_api.dataclasses import (
    NonExistentCheckParams,
    NonExistentProjectCheckParams,
)

from openstack_api.openstack_connection import OpenstackConnection
from openstack_api.openstack_query_email_base import OpenstackQueryEmailBase
from openstack_api.openstack_identity import OpenstackIdentity
from openstack_api.dataclasses import EmailQueryParams
from openstack_api.openstack_wrapper_base import OpenstackWrapperBase

from enum.server_status import ServerStatus
from exceptions.missing_mandatory_param_error import MissingMandatoryParamError


class OpenstackServer(OpenstackWrapperBase, OpenstackQueryEmailBase):
    # Lists all possible query client_side for server.list
    SEARCH_QUERY_PRESETS: List[str] = [
        "all_servers",
        "servers_older_than",
        "servers_younger_than",
        "servers_last_updated_before",
        "servers_last_updated_after",
        "servers_id_in",
        "servers_id_not_in",
        "servers_name_in",
        "servers_name_not_in",
        "servers_name_contains",
        "servers_name_not_contains",
        "servers_errored",
        "servers_shutoff",
        "servers_errored_and_shutoff",
        "servers_shutoff_before",
    ]

    # Lists possible queries client_side that don't require a project to function
    SEARCH_QUERY_PRESETS_NO_PROJECT: List[str] = [
        "servers_older_than",
        "servers_last_updated_before",
        "servers_shutoff_before",
    ]

    # Queries to be used for OpenstackQuery
    def _query_errored(self, server: Server):
        """
        Returns whether a server has error in its status
        """
        return ServerStatus.ERROR in server["status"]

    def _query_shutoff(self, server: Server):
        """
        Returns whether a server has shutoff in its status
        """
        return ServerStatus.SHUTOFF in server["status"]

    def __init__(self, connection_cls=OpenstackConnection):
        OpenstackWrapperBase.__init__(self, connection_cls)
        OpenstackQueryEmailBase.__init__(
            self,
            connection_cls,
            EmailQueryParams(
                required_email_property="user_email",
                valid_search_queries=OpenstackServer.SEARCH_QUERY_PRESETS,
                valid_search_queries_no_project=OpenstackServer.SEARCH_QUERY_PRESETS_NO_PROJECT,
            ),
        )
        self._identity_api = OpenstackIdentity(self._connection_cls)

    def get_query_property_funcs(
        self, cloud_account: str
    ) -> Dict[str, Callable[[Any], Any]]:
        """
        Returns property functions for use with OpenstackQuery.parse_properties
        :param cloud_account: The associated clouds.yaml account
        """
        return {
            "user_email": lambda a: self._query_api.get_user_prop(
                cloud_account, a["user_id"], "email"
            ),
            "user_name": lambda a: self._query_api.get_user_prop(
                cloud_account, a["user_id"], "name"
            ),
        }

    def search_all_servers(
        self, cloud_account: str, project_identifier: str, **_
    ) -> List[Server]:
        """
        Returns a list of Servers matching a given query
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :return: A list of all servers
        """
        selected_servers = []
        if project_identifier == "":
            projects = self._identity_api.list_projects(cloud_account)
        else:
            projects = [
                self._identity_api.find_mandatory_project(
                    cloud_account, project_identifier=project_identifier
                )
            ]

        with self._connection_cls(cloud_account) as conn:
            for project in projects:
                try:
                    selected_servers.extend(
                        conn.list_servers(
                            filters={
                                "all_tenants": True,
                                "project_id": project.id,
                            }
                        )
                    )
                except HttpException as err:
                    print(f"Failed to list servers in the project with id {project.id}")
                    print(err)
        return selected_servers

    def search_servers_older_than(
        self, cloud_account: str, project_identifier: str, days: int, **_
    ) -> List[Server]:
        """
        Returns a list of servers older than a given number of days
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param days: The number of days the servers should be older than
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers, self._query_api.query_datetime_before("created_at", days)
        )

    def search_servers_younger_than(
        self, cloud_account: str, project_identifier: str, days: int, **_
    ) -> List[Server]:
        """
        Returns a list of servers older than a given number of days
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param days: The number of days the servers should be older than
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers, self._query_api.query_datetime_after("created_at", days)
        )

    def search_servers_last_updated_before(
        self, cloud_account: str, project_identifier: str, days: int, **_
    ) -> List[Server]:
        """
        Returns a list of servers updated before a specified number of days in the past
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param days: The number of days before which the servers should have last been updated
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers, self._query_api.query_datetime_before("updated_at", days)
        )

    def search_servers_last_updated_after(
        self, cloud_account: str, project_identifier: str, days: int, **_
    ) -> List[Server]:
        """
        Returns a list of servers updated after a specified number of days in the past
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param days: The number of days after which the servers should have last been updated
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers, self._query_api.query_datetime_after("updated_at", days)
        )

    def search_servers_name_in(
        self, cloud_account: str, project_identifier: str, names: List[str], **_
    ) -> List[Server]:
        """
        Returns a list of servers with names in the list given
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param names: List of names that should pass the query
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers, self._query_api.query_prop_in("name", names)
        )

    def search_servers_name_not_in(
        self, cloud_account: str, project_identifier: str, names: List[str], **_
    ) -> List[Server]:
        """
        Returns a list of servers with names that aren't in the list given
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param names: List of names that should not pass the query
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers, self._query_api.query_prop_not_in("name", names)
        )

    def search_servers_name_contains(
        self, cloud_account: str, project_identifier: str, name_snippets: List[str], **_
    ) -> List[Server]:
        """
        Returns a list of servers with names containing the snippets given
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param name_snippets: List of name snippets that should be in the server names returned
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers,
            self._query_api.query_prop_contains("name", name_snippets),
        )

    def search_servers_name_not_contains(
        self, cloud_account: str, project_identifier: str, name_snippets: List[str], **_
    ) -> List[Server]:
        """
        Returns a list of servers with names that don't contain the snippets given
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param name_snippets: List of name snippets that should not be in the server names returned
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers,
            self._query_api.query_prop_not_contains("name", name_snippets),
        )

    def search_servers_id_in(
        self, cloud_account: str, project_identifier: str, ids: List[str], **_
    ) -> List[Server]:
        """
        Returns a list of servers with ids in the list given
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param ids: List of ids that should pass the query
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers,
            self._query_api.query_prop_in("id", ids),
        )

    def search_servers_id_not_in(
        self, cloud_account: str, project_identifier: str, ids: List[str], **_
    ) -> List[Server]:
        """
        Returns a list of servers with ids that aren't in the list given
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param ids: List of ids that should not pass the query
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(
            selected_servers, self._query_api.query_prop_not_in("id", ids)
        )

    def search_servers_errored(
        self, cloud_account: str, project_identifier: str, **_
    ) -> List[Server]:
        """
        Returns a list of servers that are in the error state
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(selected_servers, self._query_errored)

    def search_servers_shutoff(
        self, cloud_account: str, project_identifier: str, **_
    ) -> List[Server]:
        """
        Returns a list of servers that are shutoff
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_query(selected_servers, self._query_shutoff)

    def search_servers_errored_and_shutoff(
        self, cloud_account: str, project_identifier: str, **_
    ) -> List[Server]:
        """
        Returns a list of servers that are both errored and shutoff
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_queries(
            selected_servers,
            [self._query_shutoff, self._query_errored],
        )

    def search_servers_shutoff_before(
        self, cloud_account: str, project_identifier: str, days: int, **_
    ) -> List[Server]:
        """
        Returns a list of servers that are shutoff and were last updated before a given number of days
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :param days: The number of days before which the servers should have last updated
        :return: A list of servers matching the query
        """
        selected_servers = self.search_all_servers(cloud_account, project_identifier)

        return self._query_api.apply_queries(
            selected_servers,
            [
                self._query_shutoff,
                self._query_api.query_datetime_before("updated_at", days),
            ],
        )

    def find_non_existent_servers(
        self, cloud_account: str, project_identifier: str
    ) -> Dict[str, List[str]]:
        """
        Returns a dictionary containing the ids of projects along with a list of non-existent servers found within them
        :param cloud_account: The associated clouds.yaml account
        :param project_identifier: The project to get all associated servers with, can be empty for all projects
        :return: A dictionary containing the non-existent server ids and their projects
        """
        return self._query_api.find_non_existent_objects(
            cloud_account=cloud_account,
            project_identifier=project_identifier,
            check_params=NonExistentCheckParams(
                object_list_func=lambda conn, project: conn.list_servers(
                    detailed=False,
                    all_projects=True,
                    bare=True,
                    filters={
                        "all_tenants": True,
                        "project_id": project.id,
                    },
                ),
                object_get_func=lambda conn, object_id: conn.compute.get_server(
                    object_id
                ),
                object_id_param_name="id",
                object_project_param_name="project_id",
            ),
        )

    def find_non_existent_projects(self, cloud_account: str) -> Dict[str, List[str]]:
        """
        Returns a dictionary containing the ids of non-existent projects along with a list of server ids that
        refer to them
        :param cloud_account: The associated clouds.yaml account
        :return: A dictionary containing the non-existent projects and a list of server ids that refer to them
        """
        return self._query_api.find_non_existent_object_projects(
            cloud_account=cloud_account,
            check_params=NonExistentProjectCheckParams(
                object_list_func=lambda conn: conn.list_servers(
                    detailed=False,
                    all_projects=True,
                    bare=True,
                    filters={
                        "all_tenants": True,
                    },
                ),
                object_id_param_name="id",
                object_project_param_name="project_id",
            ),
        )

    def find_server(
        self, cloud_account: str, server_identifier: str
    ) -> Optional[Server]:
        """
        Returns a given server using the name or ID
        :param cloud_account: The associated clouds.yaml account
        :param server_identifier: The ID or name to search for
        :return: The found server or None
        """
        server_identifier = server_identifier.strip()
        if not server_identifier:
            raise MissingMandatoryParamError("A server identifier is required")

        with self._connection_cls(cloud_account) as conn:
            return conn.network.find_server(server_identifier, ignore_missing=True)

    def _wait_for_change(
        self,
        server: str,
        expected_status,
        interval_checks_seconds=10,
        timeout_seconds=600,
    ):
        """
        Function wait for a server to change state to expected state
        :param server: The server name or id
        :param expected_status: The expected server status to wait for
        :param interval_checks_seconds: Time between each check
        :param timeout_seconds: seconds before function timeout
        """
        self.conn.compute.wait_for_server(
            server,
            status=expected_status,
            interval=interval_checks_seconds,
            wait=timeout_seconds,
        )

    def shutoff_server(self, cloud_account: str, server_identifier: str) -> bool:
        """
        Shutoff Server
        :param cloud_account: The associated clouds.yaml account
        :param server_identifier: Server given Name or ID
        :return: If the server was shutdown, error message if any
        """
        server = self.find_server(cloud_account, server_identifier)
        if not server:
            raise ItemNotFoundError("The specified server was not found")

        if server["status"] is not ServerStatus.ACTIVE:
            raise RuntimeError(
                "The specified server is not ACTIVE (current status: %s)"
                % server["status"]
            )

        self.conn.compute.stop_server(server)

        try:
            self._wait_for_change(server, ServerStatus.SHUTOFF)
        except ResourceTimeout:
            raise RuntimeError("Action Timed Out, server may not have updated")
        return True

    def start_server(self, cloud_account: str, server_identifier: str):
        """
        Start Shutoff Server
        :param cloud_account: The associated clouds.yaml account
        :param server_identifier: Server given Name or ID
        :return: If the server was started properly, error message if any
        """
        server = self.find_server(cloud_account, server_identifier)
        if not server:
            raise ItemNotFoundError("The specified server was not found")

        if server["status"] is not ServerStatus.SHUTOFF:
            raise RuntimeError(
                "The specified server is not SHUTOFF (current status: %s)"
                % server["status"]
            )

        self.conn.compute.start_server(server)
        try:
            self._wait_for_change(server, ServerStatus.ACTIVE)
        except ResourceTimeout:
            raise RuntimeError("Action Timed out, server may not have updated")
        return True

    def reboot_server(self, cloud_account: str, server_identifier: str, hard_reboot_flag: bool = False) -> bool:
        """
        Reboot Server
        :param cloud_account: The associated clouds.yaml account
        :param server_identifier: Server given Name or ID
        :param hard_reboot_flag: A flag which sets if a hard reboot is requested (power-cycle)
        :return:  If the server was restarted, error message if any
        """
        server = self.find_server(cloud_account, server_identifier)
        if not server:
            raise ItemNotFoundError("The specified server was not found")

        if server["status"] is not ServerStatus.ACTIVE:
            raise RuntimeError(
                "The specified server is not ACTIVE, cannot be rebooted (current status: %s)"
                % server["status"]
            )

        self.conn.compute.reboot_server(
            server,
            "HARD" if hard_reboot_flag else "SOFT"
        )

        try:
            self._wait_for_change(server, ServerStatus.ACTIVE)
        except ResourceTimeout:
            raise RuntimeError("Action Timed out, server may not have been rebooted")
        return True
