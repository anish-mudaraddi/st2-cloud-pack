from enum import auto
from enums.query.props.prop_enum import PropEnum
from exceptions.parse_query_error import ParseQueryError
from exceptions.query_property_mapping_error import QueryPropertyMappingError


class ServerProperties(PropEnum):
    """
    An enum class for all server properties
    """

    FLAVOR_ID = auto()
    HYPERVISOR_ID = auto()
    IMAGE_ID = auto()
    PROJECT_ID = auto()
    SERVER_CREATION_DATE = auto()
    SERVER_DESCRIPTION = auto()
    SERVER_ID = auto()
    SERVER_LAST_UPDATED_DATE = auto()
    SERVER_NAME = auto()
    SERVER_STATUS = auto()
    USER_ID = auto()

    @staticmethod
    def from_string(val: str):
        """
        Converts a given string in a case-insensitive way to the enum values
        """
        try:
            return ServerProperties[val.upper()]
        except KeyError as err:
            raise ParseQueryError(
                f"Could not find Server Property {val}. "
                f"Available properties are {','.join([prop.name for prop in ServerProperties])}"
            ) from err

    @staticmethod
    def get_prop_func(prop):
        """
        Method that returns the property function if function mapping exists for a given ServerProperty Enum
        how to get specified property from an openstacksdk Server object is documented here:
        https://docs.openstack.org/openstacksdk/latest/user/resources/compute/v2/server.html#openstack.compute.v2.server.Server
        :param prop: A ServerProperty Enum for which a function may exist for
        """
        mapping = {
            ServerProperties.USER_ID: lambda a: a["user_id"],
            ServerProperties.HYPERVISOR_ID: lambda a: a["host_id"],
            ServerProperties.SERVER_ID: lambda a: a["id"],
            ServerProperties.SERVER_NAME: lambda a: a["name"],
            ServerProperties.SERVER_DESCRIPTION: lambda a: a["description"],
            ServerProperties.SERVER_STATUS: lambda a: a["status"],
            ServerProperties.SERVER_CREATION_DATE: lambda a: a["created_at"],
            ServerProperties.SERVER_LAST_UPDATED_DATE: lambda a: a["updated_at"],
            ServerProperties.FLAVOR_ID: lambda a: a["flavor_id"],
            ServerProperties.IMAGE_ID: lambda a: a["image_id"],
            ServerProperties.PROJECT_ID: lambda a: a["location"]["project"]["id"],
        }
        assert all(i in mapping for i in ServerProperties)
        for i in ServerProperties:
            assert (
                i in mapping
            ), f"Error: No prop mapping defined for ServerProperties.{i.name}"

        if prop not in ServerProperties:
            raise QueryPropertyMappingError(
                "Error: failed to get property mapping, property is not supported in ServerProperties"
            )
        return mapping[prop]

    @staticmethod
    def get_marker_prop_func():
        """
        A getter method to return marker property function for pagination
        """
        return ServerProperties.get_prop_func(ServerProperties.SERVER_ID)
