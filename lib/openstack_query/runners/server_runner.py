from typing import Optional, List, Dict
import logging

import openstack.exceptions
from openstack.compute.v2.server import Server
from openstack.exceptions import ResourceNotFound

from openstack_api.openstack_connection import OpenstackConnection
from openstack_query.runners.runner_wrapper import RunnerWrapper

from exceptions.parse_query_error import ParseQueryError
from custom_types.openstack_query.aliases import (
    ProjectIdentifier,
    ServerSideFilters,
)


logger = logging.getLogger(__name__)

# pylint:disable=too-few-public-methods


class ServerRunner(RunnerWrapper):
    """
    Runner class for openstack Server resource.
    ServerRunner encapsulates running any openstacksdk Server commands
    """

    RESOURCE_TYPE = Server

    def _parse_meta_params(
        self,
        conn: OpenstackConnection,
        from_projects: Optional[List[ProjectIdentifier]] = None,
        all_projects: bool = False,
        as_admin: bool = False,
    ) -> Dict:
        """
        This method is a helper function that will parse a set of query meta params related to openstack server queries.
        :param conn: An OpenstackConnection object - used to connect to openstack and parse meta params
        :param from_projects: A list of projects to search in
        :param all_projects: A boolean which, if true - will run query on all available projects to the user
        :param as_admin: A boolean which, if true - will run query as an admin
        """

        # raise error if ambiguous query
        if from_projects and all_projects:
            raise ParseQueryError(
                "Failed to execute query: ambiguous run params - run with either "
                "from_projects or all_projects and not both"
            )

        # default to providing servers only from the current scoped project
        curr_project_id = conn.current_project_id
        if not as_admin:
            logger.warning(
                "NOT RUNNING AS ADMIN - query will only work on the scoped project id: %s",
                curr_project_id,
            )
            if from_projects or all_projects:
                raise ParseQueryError(
                    "Failed to execute query: run_params given won't work if "
                    "you're not running as admin"
                )
            return {"projects": [curr_project_id]}

        # don't provide any projects to scope the query so it runs on all projects
        if all_projects:
            return {"all_tenants": True}

        # scope the query to user projects if from_projects not given
        # we need to validate that user is actually admin by validating that it can find each user project
        user_projects = list(conn.identity.user_projects(conn.current_user_id))
        project_list = from_projects if from_projects else user_projects
        res_list = []
        for proj in project_list:
            try:
                logger.debug(
                    "running conn.identity.find_project(%s, ignore_missing=False)", proj
                )
                project = conn.identity.find_project(proj, ignore_missing=False)["id"]
            except ResourceNotFound as exp:
                raise ParseQueryError(
                    "Failed to execute query: Failed to parse run() params"
                ) from exp
            except openstack.exceptions.ForbiddenException as exp:
                raise ParseQueryError(
                    "Failed to execute query: Not authorized to access project(s) given "
                    "- please run with admin credentials"
                ) from exp
            res_list.append(project)
        return {"all_tenants": True, "projects": res_list}

    def _run_query(
        self,
        conn: OpenstackConnection,
        filter_kwargs: Optional[ServerSideFilters] = None,
        **meta_params,
    ) -> List[Server]:
        """
        This method runs the query by running openstacksdk commands

        For ServerQuery, this command gets all projects available and iteratively finds servers that belong to that
        project
        :param conn: An OpenstackConnection object - used to connect to openstacksdk
        :param filter_kwargs: An Optional list of filter kwargs to pass to conn.compute.servers()
            to limit the servers being returned. - see https://docs.openstack.org/api-ref/compute/#list-servers
        :param meta_params: a set of meta parameters that dictates how the query is run
        """
        if not filter_kwargs:
            filter_kwargs = {}

        if "project_id" in filter_kwargs.keys() and "projects" in meta_params:
            raise ParseQueryError(
                "This query uses a preset that requires searching on project_ids "
                "- but you've provided projects to search in using from_projects meta param"
                "- please use one or the other, not both"
                "- or you are not running as admin"
            )

        if "all_tenants" in meta_params:
            filter_kwargs["all_tenants"] = meta_params["all_tenants"]

        if "projects" not in meta_params:
            logger.debug(
                "running openstacksdk command conn.compute.servers (%s)",
                ", ".join(f"{key}={value}" for key, value in filter_kwargs.items()),
            )
            return self._run_paginated_query(conn.compute.servers, dict(filter_kwargs))

        query_res = []
        project_num = len(meta_params["projects"])
        logger.debug("running query on %s projects", project_num)
        for i, project_id in enumerate(meta_params["projects"], 1):
            filter_kwargs.update({"project_id": project_id})
            logger.debug(
                "running query on project %s / %s (id: %s)", i, project_num, project_id
            )
            logger.debug(
                "running openstacksdk command conn.compute.servers (%s)",
                ", ".join(f"{key}={value}" for key, value in filter_kwargs.items()),
            )
            query_res.extend(
                self._run_paginated_query(conn.compute.servers, dict(filter_kwargs))
            )
        return query_res
