from typing import List, Optional
from enums.query.query_presets import QueryPresetsDateTime
from enums.query.sort_order import SortOrder
import openstack_query

# pylint:disable=too-many-arguments


def search_by_datetime(
    cloud_account: str,
    query_type: str,
    search_mode: str,
    property_to_search_by: str,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    properties_to_select: Optional[List[str]] = None,
    output_type: str = "to_string",
    group_by: Optional[str] = None,
    sort_by: Optional[List[str]] = None,
    **kwargs,
):
    """
    method that builds and runs a datetime-related query on Generic Resource, and then returns results.
    Uses UTC timezone
    :param cloud_account: A string representing the cloud account to use - set in clouds.ymal
    :param query_type: what Query object to use to run query with ServerQuery, UserQuery etc
    :param search_mode: A string representing what type of datetime query will be run - set as a Datetime Preset
    that the query will use
    :param property_to_search_by: A string representing a datetime property Enum that the preset will be used on
    - must be datetime compatible
    :param days: (Optional) Number of relative days in the past from now to use as threshold
    :param hours: (Optional) Number of relative hours in the past from now to use as threshold
    :param minutes: (Optional) Number of relative minutes in the past from now to use as threshold
    :param seconds: (Optional) Number of relative seconds in the past from now to use as threshold
    :param properties_to_select: list of strings representing which properties to select
    :param output_type: string representing how to output the query
    :param group_by: an optional string representing a property to group results by
    :param sort_by: an optional set of tuples representing way which properties to sort results by
    :param kwargs: A set of optional meta params to pass to the query
    """
    if all(x <= 0 for x in [days, minutes, seconds, hours]):
        raise RuntimeError(
            "At least one value for days, hours, minutes, seconds must be > 0"
        )

    query = getattr(openstack_query, query_type)()
    if not properties_to_select:
        query.select_all()
    else:
        query.select(properties_to_select)

    query.where(
        preset=QueryPresetsDateTime.from_string(search_mode),
        prop=property_to_search_by,
        args={
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
        },
    )
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
