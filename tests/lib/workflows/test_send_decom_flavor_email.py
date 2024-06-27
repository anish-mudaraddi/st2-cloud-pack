from unittest.mock import patch, call, NonCallableMock
import pytest


from enums.query.props.flavor_properties import FlavorProperties
from enums.query.props.project_properties import ProjectProperties
from enums.query.props.server_properties import ServerProperties
from enums.query.props.user_properties import UserProperties
from enums.query.query_presets import QueryPresetsGeneric
from enums.query.sort_order import SortOrder
from workflows.send_decom_flavor_email import (
    validate,
    find_user_info,
    find_servers_with_decom_flavors,
    print_email_params,
    build_email_params,
    send_decom_flavor_email,
    get_flavor_list_html,
)


def test_validate_flavor_list_empty():
    """Tests that validate raises error when flavor_name_list is empty"""
    with pytest.raises(RuntimeError):
        validate([], from_projects=None, all_projects=True)


def test_validate_not_from_projects_or_all_projects():
    """Tests that validate raises error neither from_projects or all_projects given"""
    with pytest.raises(RuntimeError):
        validate(["flavor1", "flavor2"], from_projects=None, all_projects=False)


def test_validate_empty_from_projects():
    """Tests that validate raises error neither from_projects or all_projects given"""
    with pytest.raises(RuntimeError):
        validate(["flavor1", "flavor2"], from_projects=[], all_projects=False)


def test_validate_from_projects_and_all_projects():
    """Tests that validate raises error when from_projects and all_projects are both given"""
    with pytest.raises(RuntimeError):
        validate(
            ["flavor1", "flavor2"],
            from_projects=["project1", "project2"],
            all_projects=True,
        )


def test_get_flavor_list_html():
    """tests get_flavor_list_html converts list of flavors to a html string"""
    mock_flavors = ["flavor1", "flavor2"]
    res = get_flavor_list_html(mock_flavors)
    assert res == "<ul> <li> flavor1 </li> <li> flavor2 </li> </ul>"


def test_get_flavor_list_html_empty():
    """tests get_flavor_list_html converts an empty list to an empty unorded list html string"""
    mock_flavors = []
    res = get_flavor_list_html(mock_flavors)
    assert res == "<ul>  </ul>"


def test_validate_success():
    """
    Tests validate raises no error when flavor list is provided
    and one of either all_projects or from_projects given
    """
    validate(
        ["flavor1", "flavor2"],
        from_projects=["project1", "project2"],
        all_projects=False,
    )
    validate(["flavor1", "flavor2"], from_projects=None, all_projects=True)


# pylint:disable=too-many-locals


@patch("workflows.send_decom_flavor_email.UserQuery")
def test_find_user_info_valid(mock_user_query):
    """
    Tests find_user_info where query is given a valid user id
    """
    mock_user_id = NonCallableMock()
    mock_cloud_account = NonCallableMock()
    mock_override_email = NonCallableMock()
    mock_user_query.return_value.to_props.return_value = {
        "user_name": ["foo"],
        "user_email": ["foo@example.com"],
    }
    res = find_user_info(mock_user_id, mock_cloud_account, mock_override_email)
    mock_user_query.assert_called_once()
    mock_user_query.return_value.select.assert_called_once_with(
        [UserProperties.USER_NAME, UserProperties.USER_EMAIL]
    )
    mock_user_query.return_value.where.assert_called_once_with(
        QueryPresetsGeneric.EQUAL_TO, UserProperties.USER_ID, value=mock_user_id
    )
    mock_user_query.return_value.run.assert_called_once_with(
        cloud_account=mock_cloud_account
    )
    mock_user_query.return_value.to_props.assert_called_once_with(flatten=True)

    assert res[0] == "foo"
    assert res[1] == "foo@example.com"


@patch("workflows.send_decom_flavor_email.UserQuery")
def test_find_user_info_invalid(mock_user_query):
    """
    Tests find_user_info where query is given a invalid user id
    """
    mock_user_id = NonCallableMock()
    mock_cloud_account = NonCallableMock()
    mock_override_email = NonCallableMock()
    mock_user_query.return_value.to_props.return_value = []
    res = find_user_info(mock_user_id, mock_cloud_account, mock_override_email)
    mock_user_query.assert_called_once()
    mock_user_query.return_value.select.assert_called_once_with(
        [UserProperties.USER_NAME, UserProperties.USER_EMAIL]
    )
    mock_user_query.return_value.where.assert_called_once_with(
        QueryPresetsGeneric.EQUAL_TO, UserProperties.USER_ID, value=mock_user_id
    )
    mock_user_query.return_value.run.assert_called_once_with(
        cloud_account=mock_cloud_account
    )
    mock_user_query.return_value.to_props.assert_called_once_with(flatten=True)

    assert res[0] == ""
    assert res[1] == mock_override_email


@patch("workflows.send_decom_flavor_email.UserQuery")
def test_find_user_info_no_email_address(mock_user_query):
    """
    Tests find_user_info where query result contains no email address
    """
    mock_user_id = NonCallableMock()
    mock_cloud_account = NonCallableMock()
    mock_override_email = NonCallableMock()
    mock_user_query.return_value.to_props.return_value = {
        "user_id": ["foo"],
        "user_email": [None],
    }
    res = find_user_info(mock_user_id, mock_cloud_account, mock_override_email)
    mock_user_query.assert_called_once()
    mock_user_query.return_value.select.assert_called_once_with(
        [UserProperties.USER_NAME, UserProperties.USER_EMAIL]
    )
    mock_user_query.return_value.where.assert_called_once_with(
        QueryPresetsGeneric.EQUAL_TO, UserProperties.USER_ID, value=mock_user_id
    )
    mock_user_query.return_value.run.assert_called_once_with(
        cloud_account=mock_cloud_account
    )
    mock_user_query.return_value.to_props.assert_called_once_with(flatten=True)

    assert res[0] == ""
    assert res[1] == mock_override_email


@patch("workflows.send_decom_flavor_email.FlavorQuery")
def test_find_users_with_decom_flavor_valid(mock_flavor_query):
    """
    Tests find_servers_with_decom_flavors() function
    should run a complex FlavorQuery query - chaining into servers, then users and return final query
    """
    mock_flavor_query_obj = mock_flavor_query.return_value
    mock_server_query_obj = mock_flavor_query_obj.then.return_value

    res = find_servers_with_decom_flavors(
        "test-cloud-account", ["flavor1", "flavor2"], ["project1", "project2"]
    )

    mock_flavor_query.assert_called_once()
    mock_flavor_query_obj.where.assert_any_call(
        QueryPresetsGeneric.ANY_IN,
        FlavorProperties.FLAVOR_NAME,
        values=["flavor1", "flavor2"],
    )
    mock_flavor_query_obj.run.assert_called_once_with("test-cloud-account")
    mock_flavor_query_obj.sort_by.assert_called_once_with(
        (FlavorProperties.FLAVOR_ID, SortOrder.ASC)
    )
    mock_flavor_query_obj.to_props.assert_called_once()

    mock_flavor_query_obj.then.assert_called_once_with(
        "SERVER_QUERY", keep_previous_results=True
    )
    mock_server_query_obj.run.assert_called_once_with(
        "test-cloud-account",
        as_admin=True,
        from_projects=["project1", "project2"],
        all_projects=False,
    )
    mock_server_query_obj.select.assert_called_once_with(
        [
            ServerProperties.SERVER_ID,
            ServerProperties.SERVER_NAME,
            ServerProperties.ADDRESSES,
        ]
    )
    mock_server_query_obj.to_props.assert_called_once()

    mock_server_query_obj.append_from.assert_called_once_with(
        "PROJECT_QUERY", "test-cloud-account", [ProjectProperties.PROJECT_NAME]
    )

    mock_server_query_obj.group_by.assert_called_once_with(ServerProperties.USER_ID)
    assert res == mock_server_query_obj


@patch("workflows.send_decom_flavor_email.FlavorQuery")
def test_find_users_with_decom_flavor_invalid_flavor(mock_flavor_query):
    """
    Tests that find_user_with_decom_flavors fails when provided invalid flavor name
    """
    mock_flavor_query_obj = mock_flavor_query.return_value
    mock_flavor_query_obj.to_props.return_value = None

    with pytest.raises(RuntimeError):
        find_servers_with_decom_flavors("test-cloud-account", ["invalid-flavor"])

    mock_flavor_query.assert_called_once()
    mock_flavor_query_obj.where.assert_any_call(
        QueryPresetsGeneric.ANY_IN,
        FlavorProperties.FLAVOR_NAME,
        values=["invalid-flavor"],
    )
    mock_flavor_query_obj.run.assert_called_once_with("test-cloud-account")
    mock_flavor_query_obj.sort_by.assert_called_once_with(
        (FlavorProperties.FLAVOR_ID, SortOrder.ASC)
    )
    mock_flavor_query_obj.to_props.assert_called_once()


@patch("workflows.send_decom_flavor_email.FlavorQuery")
def test_find_users_with_decom_flavor_no_servers_found(mock_flavor_query):
    """
    Tests that find_user_with_decom_flavors fails when no servers found with given flavors
    """
    mock_flavor_query_obj = mock_flavor_query.return_value
    mock_server_query_obj = mock_flavor_query_obj.then.return_value
    mock_server_query_obj.to_props.return_value = None

    with pytest.raises(RuntimeError):
        find_servers_with_decom_flavors(
            "test-cloud-account", ["flavor1", "flavor2"], ["project1", "project2"]
        )

    mock_flavor_query.assert_called_once()
    mock_flavor_query_obj.where.assert_any_call(
        QueryPresetsGeneric.ANY_IN,
        FlavorProperties.FLAVOR_NAME,
        values=["flavor1", "flavor2"],
    )
    mock_flavor_query_obj.run.assert_called_once_with("test-cloud-account")
    mock_flavor_query_obj.sort_by.assert_called_once_with(
        (FlavorProperties.FLAVOR_ID, SortOrder.ASC)
    )
    mock_flavor_query_obj.to_props.assert_called_once()

    mock_server_query_obj.run.assert_called_once_with(
        "test-cloud-account",
        as_admin=True,
        from_projects=["project1", "project2"],
        all_projects=False,
    )
    mock_server_query_obj.select.assert_called_once_with(
        [
            ServerProperties.SERVER_ID,
            ServerProperties.SERVER_NAME,
            ServerProperties.ADDRESSES,
        ]
    )
    mock_server_query_obj.to_props.assert_called_once()


def test_print_email_params():
    """
    Test print_email_params() function simply prints values
    """
    email_addr = "test@example.com"
    user_name = "John Doe"
    as_html = True
    flavor_table = "Flavor Table Content"
    decom_table = "Decom Table Content"

    with patch("builtins.print") as mock_print:
        print_email_params(email_addr, user_name, as_html, flavor_table, decom_table)

    mock_print.assert_called_once_with(
        f"Send Email To: {email_addr}\n"
        f"email_templates decom-email: username {user_name}\n"
        f"send as html: {as_html}\n"
        f"flavor table: {flavor_table}\n"
        f"decom table: {decom_table}\n"
    )


@patch("workflows.send_decom_flavor_email.EmailTemplateDetails")
@patch("workflows.send_decom_flavor_email.EmailParams")
def test_build_params(mock_email_params, mock_email_template_details):
    """
    Test build_params() function creates email params appropriately and returns them
    """

    user_name = "John Doe"
    flavor_table = "Flavor Table Content"
    decom_table = "Decom Table Content"
    email_kwargs = {"arg1": "val1", "arg2": "val2"}

    res = build_email_params(user_name, flavor_table, decom_table, **email_kwargs)
    mock_email_template_details.assert_has_calls(
        [
            call(
                template_name="decom_flavor",
                template_params={
                    "username": user_name,
                    "affected_flavors_table": flavor_table,
                    "decom_table": decom_table,
                },
            ),
            call(template_name="footer", template_params={}),
        ]
    )

    mock_email_params.assert_called_once_with(
        email_templates=[
            mock_email_template_details.return_value,
            mock_email_template_details.return_value,
        ],
        arg1="val1",
        arg2="val2",
    )

    assert res == mock_email_params.return_value


@patch("workflows.send_decom_flavor_email.validate")
@patch("workflows.send_decom_flavor_email.find_servers_with_decom_flavors")
@patch("workflows.send_decom_flavor_email.build_email_params")
@patch("workflows.send_decom_flavor_email.find_user_info")
@patch("workflows.send_decom_flavor_email.Emailer")
def test_send_decom_flavor_email_send_plaintext(
    mock_emailer,
    mock_find_user_info,
    mock_build_email_params,
    mock_find_servers,
    mock_validate,
):
    """
    Tests send_decom_flavor() function actually sends email - as_html false
    """

    flavor_name_list = ["flavor1", "flavor2"]
    limit_by_projects = NonCallableMock()
    all_projects = NonCallableMock()
    cloud_account = NonCallableMock()
    smtp_account = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}

    mock_query = mock_find_servers.return_value

    # doesn't matter what the values are here since we're just getting the keys
    mock_query.to_props.return_value = {
        "user_id1": [],
        "user_id2": [],
    }
    mock_find_user_info.side_effect = [
        ("user1", "user_email1"),
        ("user2", "user_email2"),
    ]

    send_decom_flavor_email(
        smtp_account=smtp_account,
        cloud_account=cloud_account,
        flavor_name_list=flavor_name_list,
        limit_by_projects=limit_by_projects,
        all_projects=all_projects,
        as_html=False,
        send_email=True,
        use_override=False,
        **mock_kwargs,
    )

    mock_validate.assert_called_once_with(
        flavor_name_list, limit_by_projects, all_projects
    )
    mock_find_servers.assert_called_once_with(
        cloud_account, flavor_name_list, limit_by_projects
    )
    mock_query.to_props.assert_called_once()
    mock_find_user_info.assert_has_calls(
        [
            call("user_id1", cloud_account, "cloud-support@stfc.ac.uk"),
            call("user_id2", cloud_account, "cloud-support@stfc.ac.uk"),
        ]
    )
    mock_build_email_params.assert_has_calls(
        [
            call(
                "user1",
                "flavor1, flavor2",
                mock_query.to_string.return_value,
                email_to=["user_email1"],
                as_html=False,
                email_cc=None,
                **mock_kwargs,
            ),
            call(
                "user2",
                "flavor1, flavor2",
                mock_query.to_string.return_value,
                email_to=["user_email2"],
                as_html=False,
                email_cc=None,
                **mock_kwargs,
            ),
        ]
    )

    mock_query.to_string.assert_has_calls(
        [call(groups=["user_id1"]), call(groups=["user_id2"])]
    )

    mock_emailer.assert_has_calls(
        [
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
        ]
    )


# pylint:disable=too-many-arguments
@patch("workflows.send_decom_flavor_email.validate")
@patch("workflows.send_decom_flavor_email.find_servers_with_decom_flavors")
@patch("workflows.send_decom_flavor_email.build_email_params")
@patch("workflows.send_decom_flavor_email.get_flavor_list_html")
@patch("workflows.send_decom_flavor_email.find_user_info")
@patch("workflows.send_decom_flavor_email.Emailer")
def test_send_decom_flavor_email_send_html(
    mock_emailer,
    mock_find_user_info,
    mock_get_flavor_list_html,
    mock_build_email_params,
    mock_find_servers,
    mock_validate,
):
    """
    Tests send_decom_flavor() function actually sends email - as_html True
    """

    flavor_name_list = ["flavor1", "flavor2"]
    limit_by_projects = NonCallableMock()
    all_projects = NonCallableMock()
    cloud_account = NonCallableMock()
    smtp_account = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}

    mock_query = mock_find_servers.return_value
    # doesn't matter what the values are here since we're just getting the keys
    mock_query.to_props.return_value = {
        "user_id1": [],
        "user_id2": [],
    }
    mock_find_user_info.side_effect = [
        ("user1", "user_email1"),
        ("user2", "user_email2"),
    ]

    send_decom_flavor_email(
        smtp_account=smtp_account,
        cloud_account=cloud_account,
        flavor_name_list=flavor_name_list,
        limit_by_projects=limit_by_projects,
        all_projects=all_projects,
        as_html=True,
        send_email=True,
        use_override=False,
        **mock_kwargs,
    )

    mock_validate.assert_called_once_with(
        flavor_name_list, limit_by_projects, all_projects
    )
    mock_find_servers.assert_called_once_with(
        cloud_account, flavor_name_list, limit_by_projects
    )
    mock_query.to_props.assert_called_once()
    mock_find_user_info.assert_has_calls(
        [
            call("user_id1", cloud_account, "cloud-support@stfc.ac.uk"),
            call("user_id2", cloud_account, "cloud-support@stfc.ac.uk"),
        ]
    )
    mock_build_email_params.assert_has_calls(
        [
            call(
                "user1",
                mock_get_flavor_list_html.return_value,
                mock_query.to_html.return_value,
                email_to=["user_email1"],
                as_html=True,
                email_cc=None,
                **mock_kwargs,
            ),
            call(
                "user2",
                mock_get_flavor_list_html.return_value,
                mock_query.to_html.return_value,
                email_to=["user_email2"],
                as_html=True,
                email_cc=None,
                **mock_kwargs,
            ),
        ]
    )

    mock_get_flavor_list_html.assert_has_calls(
        [call(["flavor1", "flavor2"]), call(["flavor1", "flavor2"])]
    )

    mock_query.to_html.assert_has_calls(
        [call(groups=["user_id1"]), call(groups=["user_id2"])]
    )

    mock_emailer.assert_has_calls(
        [
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
        ]
    )


@patch("workflows.send_decom_flavor_email.validate")
@patch("workflows.send_decom_flavor_email.find_servers_with_decom_flavors")
@patch("workflows.send_decom_flavor_email.find_user_info")
@patch("workflows.send_decom_flavor_email.print_email_params")
def test_send_decom_flavor_email_print(
    mock_print_email_params, mock_find_user_info, mock_find_servers, mock_validate
):
    """
    Tests send_decom_flavor() function prints when send_email=False
    """

    flavor_name_list = ["flavor1", "flavor2"]
    limit_by_projects = NonCallableMock()
    all_projects = NonCallableMock()
    cloud_account = NonCallableMock()
    smtp_account = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}

    mock_query = mock_find_servers.return_value
    # doesn't matter what the values are here since we're just getting the keys
    mock_query.to_props.return_value = {
        "user_id1": [],
        "user_id2": [],
    }
    mock_find_user_info.side_effect = [
        ("user1", "user_email1"),
        ("user2", "user_email2"),
    ]

    send_decom_flavor_email(
        smtp_account=smtp_account,
        cloud_account=cloud_account,
        flavor_name_list=flavor_name_list,
        limit_by_projects=limit_by_projects,
        all_projects=all_projects,
        as_html=True,
        send_email=False,
        use_override=False,
        **mock_kwargs,
    )

    mock_validate.assert_called_once_with(
        flavor_name_list, limit_by_projects, all_projects
    )
    mock_find_servers.assert_called_once_with(
        cloud_account, flavor_name_list, limit_by_projects
    )
    mock_query.to_props.assert_called_once()
    mock_find_user_info.assert_has_calls(
        [
            call("user_id1", cloud_account, "cloud-support@stfc.ac.uk"),
            call("user_id2", cloud_account, "cloud-support@stfc.ac.uk"),
        ]
    )
    mock_print_email_params.assert_has_calls(
        [
            call(
                "user_email1",
                "user1",
                True,
                "flavor1, flavor2",
                mock_query.to_string.return_value,
            ),
            call(
                "user_email2",
                "user2",
                True,
                "flavor1, flavor2",
                mock_query.to_string.return_value,
            ),
        ]
    )

    mock_query.to_string.assert_has_calls(
        [call(groups=["user_id1"]), call(groups=["user_id2"])]
    )


@patch("workflows.send_decom_flavor_email.validate")
@patch("workflows.send_decom_flavor_email.find_servers_with_decom_flavors")
@patch("workflows.send_decom_flavor_email.build_email_params")
@patch("workflows.send_decom_flavor_email.find_user_info")
@patch("workflows.send_decom_flavor_email.Emailer")
def test_send_decom_flavor_email_use_override(
    mock_emailer,
    mock_find_user_info,
    mock_build_email_params,
    mock_find_servers,
    mock_validate,
):
    """
    Tests send_decom_flavor() function sends email to override email - when use_override set
    """

    flavor_name_list = ["flavor1", "flavor2"]
    limit_by_projects = NonCallableMock()
    all_projects = NonCallableMock()
    cloud_account = NonCallableMock()
    smtp_account = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}

    mock_query = mock_find_servers.return_value
    # doesn't matter what the values are here since we're just getting the keys
    mock_query.to_props.return_value = {
        "user_id1": [],
        "user_id2": [],
    }
    mock_find_user_info.side_effect = [
        ("user1", "user_email1"),
        ("user2", "user_email2"),
    ]
    override_email_address = "example@example.com"

    send_decom_flavor_email(
        smtp_account=smtp_account,
        cloud_account=cloud_account,
        flavor_name_list=flavor_name_list,
        limit_by_projects=limit_by_projects,
        all_projects=all_projects,
        as_html=False,
        send_email=True,
        use_override=True,
        override_email_address=override_email_address,
        **mock_kwargs,
    )

    mock_validate.assert_called_once_with(
        flavor_name_list, limit_by_projects, all_projects
    )
    mock_find_servers.assert_called_once_with(
        cloud_account, flavor_name_list, limit_by_projects
    )
    mock_query.to_props.assert_called_once()
    mock_find_user_info.assert_has_calls(
        [
            call("user_id1", cloud_account, "example@example.com"),
            call("user_id2", cloud_account, "example@example.com"),
        ]
    )

    mock_build_email_params.assert_has_calls(
        [
            call(
                "user1",
                "flavor1, flavor2",
                mock_query.to_string.return_value,
                email_to=[override_email_address],
                as_html=False,
                email_cc=None,
                **mock_kwargs,
            ),
            call(
                "user2",
                "flavor1, flavor2",
                mock_query.to_string.return_value,
                email_to=[override_email_address],
                as_html=False,
                email_cc=None,
                **mock_kwargs,
            ),
        ]
    )

    mock_query.to_string.assert_has_calls(
        [call(groups=["user_id1"]), call(groups=["user_id2"])]
    )

    mock_emailer.assert_has_calls(
        [
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
        ]
    )
