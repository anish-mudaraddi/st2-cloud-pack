from typing import List, Optional, Union

from openstack_query import FlavorQuery, UserQuery

from enums.query.sort_order import SortOrder
from enums.cloud_domains import CloudDomains
from enums.query.query_presets import QueryPresetsGeneric
from enums.query.props.flavor_properties import FlavorProperties
from enums.query.props.server_properties import ServerProperties
from enums.query.props.project_properties import ProjectProperties
from enums.query.props.user_properties import UserProperties

from structs.email.smtp_account import SMTPAccount
from structs.email.email_template_details import EmailTemplateDetails
from structs.email.email_params import EmailParams

from email_api.emailer import Emailer


def get_flavor_list_html(flavor_list: List[str]):
    """
    prints flavor list in html format (as unordered list)
    :parma flavor_list a list of flavor strings
    """
    unordered_list = "<ul> "
    unordered_list += " ".join(f"<li> {item} </li>" for item in flavor_list)
    unordered_list += " </ul>"
    return unordered_list


def validate(
    flavor_name_list: List[str],
    from_projects: List[str] = None,
    all_projects: bool = False,
):
    """
    Validate incoming kwargs to ensure they are valid
    :param flavor_name_list: list of flavor names to limit query by
    :param from_projects: list of projects to limit query by
    :param all_projects: a flag which if set, will run the query on all projects
    """
    if not flavor_name_list:
        raise RuntimeError("please provide a list of flavor names to decommission")

    if from_projects and all_projects:
        raise RuntimeError(
            "given both project list and all_projects flag - please choose only one"
        )

    if not from_projects and not all_projects:
        raise RuntimeError(
            "please provide either a list of project identifiers or with flag 'all_projects' to run globally"
        )


def find_servers_with_decom_flavors(
    cloud_account: str,
    flavor_name_list: List[str],
    from_projects: Optional[List[str]] = None,
):
    """
    Use QueryAPI to run the query to find decom flavors
    :param cloud_account: string represents cloud account to use
    :param flavor_name_list: A list of flavor names to be decommissioned
    :param from_projects: A list of project identifiers to limit search in
    """

    flavor_query = FlavorQuery()
    flavor_query.where(
        QueryPresetsGeneric.ANY_IN,
        FlavorProperties.FLAVOR_NAME,
        values=flavor_name_list,
    )
    flavor_query.run(cloud_account)
    flavor_query.sort_by((FlavorProperties.FLAVOR_ID, SortOrder.ASC))

    if not flavor_query.to_props():
        raise RuntimeError(
            f"None of the Flavors provided {', '.join(flavor_name_list)} were found"
        )

    # find the VMs using flavors we found from the flavor query
    server_query = flavor_query.then("SERVER_QUERY", keep_previous_results=True)
    server_query.run(
        cloud_account,
        as_admin=True,
        from_projects=from_projects if from_projects else None,
        all_projects=not from_projects,
    )
    server_query.select(
        [
            ServerProperties.SERVER_ID,
            ServerProperties.SERVER_NAME,
            ServerProperties.ADDRESSES,
        ]
    )

    if not server_query.to_props():
        raise RuntimeError(
            f"No servers found with flavors {', '.join(flavor_name_list)} on projects "
            f"{','.join(from_projects) if from_projects else '[all projects]'}"
        )

    server_query.append_from(
        "PROJECT_QUERY", cloud_account, [ProjectProperties.PROJECT_NAME]
    )
    server_query.group_by(ServerProperties.USER_ID)

    return server_query


def print_email_params(
    email_addr: str, user_name: str, as_html: bool, flavor_table: str, decom_table: str
):
    """
    Print email params instead of sending the email
    :param email_addr: email address to send to
    :param user_name: name of user in openstack
    :param as_html: A boolean which if selected will send an email, otherwise prints email details only
    :param flavor_table: a table representing decommissioned flavors
    :param decom_table: a table representing info found in openstack
    about VMs running with decommissioned flavors
    """
    print(
        f"Send Email To: {email_addr}\n"
        f"email_templates decom-email: username {user_name}\n"
        f"send as html: {as_html}\n"
        f"flavor table: {flavor_table}\n"
        f"decom table: {decom_table}\n"
    )


def build_email_params(
    user_name: str, flavor_table: str, decom_table: str, **email_kwargs
):
    """
    build email params dataclass which will be used to configure how to send the email
    :param user_name: name of user in openstack
    :param flavor_table: a table representing decommissioned flavors
    :param decom_table: a table representing info found in openstack about VMs
        running with decommissioned flavors
    :param email_kwargs: a set of email kwargs to pass to EmailParams
    """
    body = EmailTemplateDetails(
        template_name="decom_flavor",
        template_params={
            "username": user_name,
            "affected_flavors_table": flavor_table,
            "decom_table": decom_table,
        },
    )

    footer = EmailTemplateDetails(template_name="footer", template_params={})

    return EmailParams(email_templates=[body, footer], **email_kwargs)


def find_user_info(user_id, cloud_account, override_email_address):
    """
    run a UserQuery to find the email address and user name associated for a user id.
    :param user_id: the openstack user id to find email address for
    :param override_email_address: email address to return if no email address found via UserQuery
    """
    user_query = UserQuery()
    user_query.select([UserProperties.USER_NAME, UserProperties.USER_EMAIL])
    user_query.where(
        QueryPresetsGeneric.EQUAL_TO, UserProperties.USER_ID, value=user_id
    )
    user_query.run(cloud_account=cloud_account)
    res = user_query.to_props(flatten=True)
    if not res or not res["user_email"][0]:
        return "", override_email_address
    return res["user_name"][0], res["user_email"][0]


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
def send_decom_flavor_email(
    smtp_account: SMTPAccount,
    cloud_account: Union[CloudDomains, str],
    flavor_name_list: List[str],
    limit_by_projects: Optional[List[str]] = None,
    all_projects: bool = False,
    as_html: bool = False,
    send_email: bool = False,
    use_override: bool = False,
    override_email_address: Optional[str] = "cloud-support@stfc.ac.uk",
    cc_cloud_support: bool = False,
    **email_params_kwargs,
):
    """
    Sends an email to each user who owns one or more VMs that have a flavor that is to be decommissioned.
    This email will contain a notice to delete or rebuild the VM
    :param smtp_account: (SMTPAccount): SMTP config
    :param cloud_account: string represents cloud account to use
    :param flavor_name_list: A list of flavor names to be decommissioned
    :param limit_by_projects: A list of project names or ids to limit search in
    :param all_projects: A boolean which if selected will search in all projects
    :param send_email: Actually send the email instead of printing what will be sent
    :param as_html: Send email as html
    :param use_override: flag if set will use override email address
    :param override_email_address: an overriding email address to use if override_email set
    :param cc_cloud_support: flag if set will cc cloud-support email address to each generated email
    :param email_params_kwargs: see EmailParams dataclass class docstring
    """
    validate(flavor_name_list, limit_by_projects, all_projects)
    server_query = find_servers_with_decom_flavors(
        cloud_account, flavor_name_list, limit_by_projects
    )

    for user_id in server_query.to_props().keys():
        # if email_address not found - send to override_email_address
        # also send to override_email_address if override_email set
        user_name, email_addr = find_user_info(
            user_id, cloud_account, override_email_address
        )
        send_to = [email_addr]
        if use_override:
            send_to = [override_email_address]

        if not send_email:
            print_email_params(
                send_to[0],
                user_name,
                as_html,
                ", ".join(flavor_name_list),
                server_query.to_string(groups=[user_id]),
            )

        else:
            email_params = build_email_params(
                user_name,
                (
                    ", ".join(flavor_name_list)
                    if not as_html
                    else get_flavor_list_html(flavor_name_list)
                ),
                (
                    server_query.to_string(groups=[user_id])
                    if not as_html
                    else server_query.to_html(groups=[user_id])
                ),
                email_to=send_to,
                as_html=as_html,
                email_cc=("cloud-support@stfc.ac.uk",) if cc_cloud_support else None,
                **email_params_kwargs,
            )
            Emailer(smtp_account).send_emails([email_params])
