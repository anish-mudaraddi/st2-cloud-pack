from typing import List, Optional
from enums.query.sort_order import SortOrder
import openstack_query

# pylint:disable=too-many-arguments


def list_all_openstack(
    cloud_account: str,
    query_type: str,
    properties_to_select: Optional[List[str]] = None,
    output_type: str = "to_string",
    group_by: Optional[str] = None,
    sort_by: Optional[List[str]] = None,
    **kwargs,
):
    """
    method that returns a list of all resources
    :param cloud_account: A string representing the cloud account to use - set in clouds.ymal
    :param query_type: what Query object to use to run query with ServerQuery, UserQuery etc
    :param properties_to_select: list of strings representing which properties to select
    :param output_type: string representing how to output the query
    :param group_by: an optional string representing a property to group results by
    :param sort_by: an optional set of tuples representing way which properties to sort results by
    :param kwargs: A set of optional meta params to pass to the query

    """
    query = getattr(openstack_query, query_type)()

    if not properties_to_select:
        query.select_all()
    else:
        query.select(properties_to_select)

    if sort_by:
        query.sort_by([(p, SortOrder.DESC) for p in sort_by])
    if group_by:
        query.group_by(group_by)

    query.run(cloud_account, **kwargs)
    return {
        "to_html": query.to_html(),
        "to_string": query.to_string(),
        "to_objects": query.to_objects(),
        "to_props": query.to_props(),
    }[output_type]
