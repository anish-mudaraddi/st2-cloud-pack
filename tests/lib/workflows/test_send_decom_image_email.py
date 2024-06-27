from unittest.mock import patch, call, NonCallableMock
import pytest

from workflows.send_decom_image_email import (
    get_affected_images_html,
    get_affected_images_plaintext,
    get_image_info,
    list_to_regex_pattern,
    find_servers_with_decom_images,
    print_email_params,
    build_email_params,
    find_user_info,
    send_decom_image_email,
)


def test_get_affected_images_html():
    """
    Tests that get_affected_images_html returns a html formatted list given valid inputs
    """
    res = get_affected_images_html(
        [
            {"name": "img1", "eol": "2024/06/30", "upgrade": "new-img1"},
            {"name": "img2", "eol": "2024/06/29", "upgrade": "new-img2"},
        ]
    )
    assert res == (
        "<table>"
        "<tr><th>Affected Images</th><th>EOL Date</th><th>Recommended Upgraded Image</th></tr>"
        "<tr><td>img1</td><td>2024/06/30</td><td>new-img1</td></tr>"
        "<tr><td>img2</td><td>2024/06/29</td><td>new-img2</td></tr>"
        "</table>"
    )


@patch("workflows.send_decom_image_email.tabulate")
def test_get_affected_images_plaintext(mock_tabulate):
    """
    Tests that get_affected_plaintext calls tabulate correctly
    """
    mock_image_info = [
        {"name": "img1", "eol": "2024/06/30", "upgrade": "new-img1"},
        {"name": "img2", "eol": "2024/06/29", "upgrade": "new-img2"},
    ]
    res = get_affected_images_plaintext(mock_image_info)
    mock_tabulate.assert_called_once_with(
        mock_image_info,
        headers={
            "name": "Affected Images",
            "eol": "EOL Date",
            "upgrade": "Recommended Upgrade Image",
        },
        tablefmt="plain",
    )
    assert res == mock_tabulate.return_value


def test_get_image_info_image_list_empty():
    """Tests that get_image_info returns error when passed empty image name list"""
    with pytest.raises(RuntimeError):
        get_image_info([], [], [])


def test_get_image_info_eol_list_unequal():
    """Tests that get_image_info returns error when lists passed are unequal (eol)"""
    with pytest.raises(RuntimeError):
        get_image_info(["img1"], [], ["up-img1"])


def test_get_image_info_upg_list_unequal():
    """Tests that get_image_info returns error when lists passed are unequal (upgrade_list)"""
    with pytest.raises(RuntimeError):
        get_image_info(["img1"], ["2024/01/01"], ["up-img1", "up-img2"])


def test_get_image_info_eol_invalid():
    """Tests that get_image_info returns error when eol not passed as YYYY/MM/DD"""
    with pytest.raises(RuntimeError):
        get_image_info(["img1"], ["24th June 2024"], ["up-img1"])


def test_get_image_info_valid():
    """Tests that get_image_info returns parsed list of dicts when inputs are valid"""
    res = get_image_info(
        ["img1", "img2"], ["2024/06/24", "2024/01/01"], ["up-img1", ""]
    )
    assert res == [
        {"name": "img1", "eol": "2024/06/24", "upgrade": "up-img1"},
        {"name": "img2", "eol": "2024/01/01", "upgrade": "None (deletion recommended)"},
    ]


def test_list_to_regex_pattern():
    """tests list_to_regex_pattern creates regex pattern from list"""
    mock_list = ["img1", "img2", "img3"]
    res = list_to_regex_pattern(mock_list)
    assert res == "(.*img1|.*img2|.*img3)"


# pylint:disable=too-many-locals
@patch("workflows.send_decom_image_email.UserQuery")
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
        ["name", "email_address"]
    )
    mock_user_query.return_value.where.assert_called_once_with(
        "equal_to", "id", value=mock_user_id
    )
    mock_user_query.return_value.run.assert_called_once_with(
        cloud_account=mock_cloud_account
    )
    mock_user_query.return_value.to_props.assert_called_once_with(flatten=True)

    assert res[0] == "foo"
    assert res[1] == "foo@example.com"


@patch("workflows.send_decom_image_email.UserQuery")
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
        ["name", "email_address"]
    )
    mock_user_query.return_value.where.assert_called_once_with(
        "equal_to", "id", value=mock_user_id
    )
    mock_user_query.return_value.run.assert_called_once_with(
        cloud_account=mock_cloud_account
    )
    mock_user_query.return_value.to_props.assert_called_once_with(flatten=True)

    assert res[0] == ""
    assert res[1] == mock_override_email


@patch("workflows.send_decom_image_email.UserQuery")
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
        ["name", "email_address"]
    )
    mock_user_query.return_value.where.assert_called_once_with(
        "equal_to", "id", value=mock_user_id
    )
    mock_user_query.return_value.run.assert_called_once_with(
        cloud_account=mock_cloud_account
    )
    mock_user_query.return_value.to_props.assert_called_once_with(flatten=True)

    assert res[0] == ""
    assert res[1] == mock_override_email


@patch("workflows.send_decom_image_email.ImageQuery")
@patch("workflows.send_decom_image_email.list_to_regex_pattern")
def test_find_servers_with_decom_images_valid(mock_list_to_regex, mock_image_query):
    """
    Tests find_servers_with_decom_images() function
    should run a complex ImageQuery query - chaining into servers and appending project name
    """
    mock_image_query_obj = mock_image_query.return_value
    mock_server_query_obj = mock_image_query_obj.then.return_value

    res = find_servers_with_decom_images(
        "test-cloud-account", ["img1", "img2"], ["project1", "project2"]
    )
    mock_image_query.assert_called_once()
    mock_list_to_regex.assert_called_once_with(["img1", "img2"])
    mock_image_query_obj.where.assert_called_once_with(
        "matches_regex",
        "name",
        value=mock_list_to_regex.return_value,
    )

    mock_image_query_obj.run.assert_called_once_with(
        "test-cloud-account",
        as_admin=True,
        from_projects=["project1", "project2"],
        all_projects=False,
    )
    mock_image_query_obj.sort_by.assert_called_once_with(
        [("id", "ascending"), ("name", "ascending")]
    )
    mock_image_query_obj.to_props.assert_called_once()
    mock_image_query_obj.then.assert_called_once_with(
        "server_query", keep_previous_results=True
    )

    mock_server_query_obj.run.assert_called_once_with(
        "test-cloud-account",
        as_admin=True,
        from_projects=["project1", "project2"],
        all_projects=False,
    )
    mock_server_query_obj.select.assert_called_once_with(["id", "name", "addresses"])
    mock_server_query_obj.to_props.assert_called_once()

    mock_server_query_obj.append_from.assert_called_once_with(
        "PROJECT_QUERY", "test-cloud-account", ["name"]
    )
    mock_server_query_obj.group_by.assert_called_once_with("user_id")
    assert res == mock_server_query_obj


@patch("workflows.send_decom_image_email.ImageQuery")
@patch("workflows.send_decom_image_email.list_to_regex_pattern")
def test_find_servers_with_decom_images_invalid_images(
    mock_list_to_regex, mock_image_query
):
    """
    Tests that find_servers_with_decom_images fails when provided invalid image name
    """

    mock_image_query_obj = mock_image_query.return_value
    mock_image_query_obj.to_props.return_value = None

    with pytest.raises(RuntimeError):
        find_servers_with_decom_images("test-cloud-account", ["invalid-img"])

    mock_image_query.assert_called_once()
    mock_image_query_obj.where.assert_called_once_with(
        "matches_regex",
        "name",
        value=mock_list_to_regex.return_value,
    )

    mock_image_query_obj.run.assert_called_once_with(
        "test-cloud-account",
        as_admin=True,
        from_projects=None,
        all_projects=True,
    )
    mock_image_query_obj.sort_by.assert_called_once_with(
        [("id", "ascending"), ("name", "ascending")]
    )
    mock_image_query_obj.to_props.assert_called_once()


@patch("workflows.send_decom_image_email.ImageQuery")
@patch("workflows.send_decom_image_email.list_to_regex_pattern")
def test_find_servers_with_decom_images_no_servers_found(
    mock_list_to_regex, mock_image_query
):
    """
    Tests that find_servers_with_decom_images fails when provided invalid image name
    """

    mock_image_query_obj = mock_image_query.return_value
    mock_server_query_obj = mock_image_query_obj.then.return_value
    mock_server_query_obj.to_props.return_value = None

    with pytest.raises(RuntimeError):
        find_servers_with_decom_images(
            "test-cloud-account", ["img1", "img2"], ["project1", "project2"]
        )

    mock_image_query.assert_called_once()
    mock_list_to_regex.assert_called_once_with(["img1", "img2"])
    mock_image_query_obj.where.assert_called_once_with(
        "matches_regex",
        "name",
        value=mock_list_to_regex.return_value,
    )

    mock_image_query_obj.run.assert_called_once_with(
        "test-cloud-account",
        as_admin=True,
        from_projects=["project1", "project2"],
        all_projects=False,
    )
    mock_image_query_obj.sort_by.assert_called_once_with(
        [("id", "ascending"), ("name", "ascending")]
    )
    mock_image_query_obj.to_props.assert_called_once()

    mock_server_query_obj.run.assert_called_once_with(
        "test-cloud-account",
        as_admin=True,
        from_projects=["project1", "project2"],
        all_projects=False,
    )
    mock_server_query_obj.select.assert_called_once_with(["id", "name", "addresses"])
    mock_server_query_obj.to_props.assert_called_once()


def test_print_email_params():
    """
    Test print_email_params() function simply prints values
    """
    email_addr = "test@example.com"
    user_name = "John Doe"
    as_html = True
    image_table = "Image Table Content"
    decom_table = "Decom Table Content"

    with patch("builtins.print") as mock_print:
        print_email_params(email_addr, user_name, as_html, image_table, decom_table)

    mock_print.assert_called_once_with(
        f"Send Email To: {email_addr}\n"
        f"email_templates decom-email: username {user_name}\n"
        f"send as html: {as_html}\n"
        f"affected image table: {image_table}\n"
        f"decom table: {decom_table}\n"
    )


@patch("workflows.send_decom_image_email.EmailTemplateDetails")
@patch("workflows.send_decom_image_email.EmailParams")
def test_build_params(mock_email_params, mock_email_template_details):
    """
    Test build_params() function creates email params appropriately and returns them
    """

    user_name = "John Doe"
    image_table = "Image Table Content"
    decom_table = "Decom Table Content"
    email_kwargs = {"arg1": "val1", "arg2": "val2"}

    res = build_email_params(user_name, image_table, decom_table, **email_kwargs)
    mock_email_template_details.assert_has_calls(
        [
            call(
                template_name="decom_image",
                template_params={
                    "username": user_name,
                    "affected_images_table": image_table,
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


# pylint:disable=too-many-arguments
@patch("workflows.send_decom_image_email.get_image_info")
@patch("workflows.send_decom_image_email.find_servers_with_decom_images")
@patch("workflows.send_decom_image_email.find_user_info")
@patch("workflows.send_decom_image_email.get_affected_images_plaintext")
@patch("workflows.send_decom_image_email.build_email_params")
@patch("workflows.send_decom_image_email.Emailer")
def test_send_decom_image_email_send_plaintext(
    mock_emailer,
    mock_build_email_params,
    mock_get_affected_images_plaintext,
    mock_find_user_info,
    mock_find_servers,
    mock_get_image_info,
):
    """
    Tests send_decom_image() function actually sends email - as_html false
    """
    image_name_list = ["img1", "img2"]
    image_eol_list = NonCallableMock()
    image_upgrade_list = NonCallableMock()
    limit_by_projects = ["project1", "project2"]
    all_projects = False
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

    send_decom_image_email(
        smtp_account=smtp_account,
        cloud_account=cloud_account,
        image_name_list=image_name_list,
        image_eol_list=image_eol_list,
        image_upgrade_list=image_upgrade_list,
        limit_by_projects=limit_by_projects,
        all_projects=all_projects,
        as_html=False,
        send_email=True,
        use_override=False,
        **mock_kwargs,
    )

    mock_get_image_info.assert_called_once_with(
        image_name_list, image_eol_list, image_upgrade_list
    )
    mock_find_servers.assert_called_once_with(
        cloud_account, image_name_list, limit_by_projects
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
                mock_get_affected_images_plaintext.return_value,
                mock_query.to_string.return_value,
                email_to=["user_email1"],
                as_html=False,
                email_cc=None,
                **mock_kwargs,
            ),
            call(
                "user2",
                mock_get_affected_images_plaintext.return_value,
                mock_query.to_string.return_value,
                email_to=["user_email2"],
                as_html=False,
                email_cc=None,
                **mock_kwargs,
            ),
        ]
    )

    mock_query.to_string.assert_has_calls(
        [
            call(groups=["user_id1"], include_group_titles=False),
            call(groups=["user_id2"], include_group_titles=False),
        ]
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
@patch("workflows.send_decom_image_email.get_image_info")
@patch("workflows.send_decom_image_email.find_servers_with_decom_images")
@patch("workflows.send_decom_image_email.find_user_info")
@patch("workflows.send_decom_image_email.get_affected_images_html")
@patch("workflows.send_decom_image_email.build_email_params")
@patch("workflows.send_decom_image_email.Emailer")
def test_send_decom_image_email_send_html(
    mock_emailer,
    mock_build_email_params,
    mock_get_affected_images_html,
    mock_find_user_info,
    mock_find_servers,
    mock_get_image_info,
):
    """
    Tests send_decom_image() function actually sends email - as_html True
    """

    image_name_list = ["img1", "img2"]
    image_eol_list = NonCallableMock()
    image_upgrade_list = NonCallableMock()
    limit_by_projects = ["project1", "project2"]
    all_projects = False
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

    send_decom_image_email(
        smtp_account=smtp_account,
        cloud_account=cloud_account,
        image_name_list=image_name_list,
        image_eol_list=image_eol_list,
        image_upgrade_list=image_upgrade_list,
        limit_by_projects=limit_by_projects,
        all_projects=all_projects,
        as_html=True,
        send_email=True,
        use_override=False,
        **mock_kwargs,
    )

    mock_get_image_info.assert_called_once_with(
        image_name_list, image_eol_list, image_upgrade_list
    )
    mock_find_servers.assert_called_once_with(
        cloud_account, image_name_list, limit_by_projects
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
                mock_get_affected_images_html.return_value,
                mock_query.to_html.return_value,
                email_to=["user_email1"],
                as_html=True,
                email_cc=None,
                **mock_kwargs,
            ),
            call(
                "user2",
                mock_get_affected_images_html.return_value,
                mock_query.to_html.return_value,
                email_to=["user_email2"],
                as_html=True,
                email_cc=None,
                **mock_kwargs,
            ),
        ]
    )

    mock_query.to_html.assert_has_calls(
        [
            call(groups=["user_id1"], include_group_titles=False),
            call(groups=["user_id2"], include_group_titles=False),
        ]
    )

    mock_emailer.assert_has_calls(
        [
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
        ]
    )


@patch("workflows.send_decom_image_email.get_image_info")
@patch("workflows.send_decom_image_email.find_servers_with_decom_images")
@patch("workflows.send_decom_image_email.find_user_info")
@patch("workflows.send_decom_image_email.get_affected_images_plaintext")
@patch("workflows.send_decom_image_email.print_email_params")
def test_send_decom_image_email_print(
    mock_print_email_params,
    mock_get_affected_images_plaintext,
    mock_find_user_info,
    mock_find_servers,
    mock_get_image_info,
):
    """
    Tests send_decom_image() function prints when send_email=False
    """

    image_name_list = ["img1", "img2"]
    image_eol_list = NonCallableMock()
    image_upgrade_list = NonCallableMock()
    limit_by_projects = ["project1", "project2"]
    all_projects = False
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

    send_decom_image_email(
        smtp_account=smtp_account,
        cloud_account=cloud_account,
        image_name_list=image_name_list,
        image_eol_list=image_eol_list,
        image_upgrade_list=image_upgrade_list,
        limit_by_projects=limit_by_projects,
        all_projects=all_projects,
        as_html=True,
        send_email=False,
        use_override=False,
        **mock_kwargs,
    )

    mock_get_image_info.assert_called_once_with(
        image_name_list, image_eol_list, image_upgrade_list
    )
    mock_find_servers.assert_called_once_with(
        cloud_account, image_name_list, limit_by_projects
    )
    mock_query.to_props.assert_called_once()
    mock_find_user_info.assert_has_calls(
        [
            call("user_id1", cloud_account, "cloud-support@stfc.ac.uk"),
            call("user_id2", cloud_account, "cloud-support@stfc.ac.uk"),
        ]
    )

    mock_find_servers.assert_called_once_with(
        cloud_account, image_name_list, limit_by_projects
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
                mock_get_affected_images_plaintext.return_value,
                mock_query.to_string.return_value,
            ),
            call(
                "user_email2",
                "user2",
                True,
                mock_get_affected_images_plaintext.return_value,
                mock_query.to_string.return_value,
            ),
        ]
    )

    mock_query.to_string.assert_has_calls(
        [
            call(groups=["user_id1"], include_group_titles=False),
            call(groups=["user_id2"], include_group_titles=False),
        ]
    )


@patch("workflows.send_decom_image_email.get_image_info")
@patch("workflows.send_decom_image_email.find_servers_with_decom_images")
@patch("workflows.send_decom_image_email.find_user_info")
@patch("workflows.send_decom_image_email.get_affected_images_plaintext")
@patch("workflows.send_decom_image_email.build_email_params")
@patch("workflows.send_decom_image_email.Emailer")
def test_send_decom_image_email_use_override(
    mock_emailer,
    mock_build_email_params,
    mock_get_affected_images_plaintext,
    mock_find_user_info,
    mock_find_servers,
    mock_get_image_info,
):
    """
    Tests send_decom_image() function sends email to override email - when use_override set
    """
    image_name_list = ["img1", "img2"]
    image_eol_list = NonCallableMock()
    image_upgrade_list = NonCallableMock()
    limit_by_projects = ["project1", "project2"]
    all_projects = False
    cloud_account = NonCallableMock()
    smtp_account = NonCallableMock()
    mock_kwargs = {"arg1": "val1", "arg2": "val2"}
    override_email_address = "example@example.com"

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

    send_decom_image_email(
        smtp_account=smtp_account,
        cloud_account=cloud_account,
        image_name_list=image_name_list,
        image_eol_list=image_eol_list,
        image_upgrade_list=image_upgrade_list,
        limit_by_projects=limit_by_projects,
        all_projects=all_projects,
        as_html=False,
        send_email=True,
        use_override=True,
        override_email_address=override_email_address,
        **mock_kwargs,
    )

    mock_get_image_info.assert_called_once_with(
        image_name_list, image_eol_list, image_upgrade_list
    )
    mock_find_servers.assert_called_once_with(
        cloud_account, image_name_list, limit_by_projects
    )
    mock_query.to_props.assert_called_once()
    mock_find_user_info.assert_has_calls(
        [
            call("user_id1", cloud_account, override_email_address),
            call("user_id2", cloud_account, override_email_address),
        ]
    )

    mock_build_email_params.assert_has_calls(
        [
            call(
                "user1",
                mock_get_affected_images_plaintext.return_value,
                mock_query.to_string.return_value,
                email_to=[override_email_address],
                as_html=False,
                email_cc=None,
                **mock_kwargs,
            ),
            call(
                "user2",
                mock_get_affected_images_plaintext.return_value,
                mock_query.to_string.return_value,
                email_to=[override_email_address],
                as_html=False,
                email_cc=None,
                **mock_kwargs,
            ),
        ]
    )

    mock_query.to_string.assert_has_calls(
        [
            call(groups=["user_id1"], include_group_titles=False),
            call(groups=["user_id2"], include_group_titles=False),
        ]
    )

    mock_emailer.assert_has_calls(
        [
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
            call(smtp_account),
            call().send_emails([mock_build_email_params.return_value]),
        ]
    )


def test_raise_error_when_both_from_projects_all_projects():
    """Tests that send_decom_image_email raises error if both from_projects or all_projects given"""
    with pytest.raises(RuntimeError):
        send_decom_image_email(
            smtp_account="",
            cloud_account="",
            image_name_list=[],
            image_eol_list=[],
            image_upgrade_list=[],
            all_projects=True,
            limit_by_projects=["proj1", "proj2"],
        )


def test_raise_error_when_neither_from_projects_all_projects():
    """Tests that send_decom_image_email raises error if neither from_projects or all_projects given"""
    with pytest.raises(RuntimeError):
        send_decom_image_email(
            smtp_account="",
            cloud_account="",
            image_name_list=[],
            image_eol_list=[],
            image_upgrade_list=[],
        )
