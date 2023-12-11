import pytest

from enums.query.query_types import QueryTypes
from exceptions.parse_query_error import ParseQueryError


@pytest.mark.parametrize(
    "query_type",
    [
        "Flavor_Query",
        "FlAvOr_Query",
        "flavor_query",
        "flavor",
        "flavors",
        "query_flavors",
        "to_flavor_query",
    ],
)
def test_flavor_query_serialization(query_type):
    """
    Tests that variants of FLAVOR_QUERY can be serialized
    """
    assert QueryTypes.from_string(query_type) is QueryTypes.FLAVOR_QUERY


@pytest.mark.parametrize(
    "query_type",
    [
        "Server_Query",
        "SeRvEr_QuErY",
        "server_query",
        "server",
        "servers",
        "query_servers",
        "to_server_query",
    ],
)
def test_server_query_serialization(query_type):
    """
    Tests that variants of SERVER_QUERY can be serialized
    """
    assert QueryTypes.from_string(query_type) is QueryTypes.SERVER_QUERY


@pytest.mark.parametrize(
    "query_type",
    [
        "Project_Query",
        "PrOjEcT_Query",
        "project_query",
        "project",
        "projects",
        "query_projects",
        "to_project_query",
    ],
)
def test_project_query_serialization(query_type):
    """
    Tests that variants of PROJECT_QUERY can be serialized
    """
    assert QueryTypes.from_string(query_type) is QueryTypes.PROJECT_QUERY


@pytest.mark.parametrize(
    "query_type",
    [
        "User_Query",
        "UsEr_QuEry",
        "user_query",
        "user",
        "users",
        "query_users",
        "to_user_query",
    ],
)
def test_user_query_serialization(query_type):
    """
    Tests that variants of USER_QUERY can be serialized
    """
    assert QueryTypes.from_string(query_type) is QueryTypes.USER_QUERY


def test_invalid_serialization():
    """
    Tests that error is raised when passes invalid string
    """
    with pytest.raises(ParseQueryError):
        QueryTypes.from_string("some-invalid-string")
