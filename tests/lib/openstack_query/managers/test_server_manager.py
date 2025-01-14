import unittest
from unittest.mock import MagicMock, patch

from openstack_query.managers.server_manager import ServerManager


@patch("openstack_query.managers.query_manager.QueryManager._build_and_run_query")
@patch("openstack_query.managers.server_manager.QueryOutputDetails")
class ServerManagerTests(unittest.TestCase):
    """
    Runs various tests to ensure that ServerManager class methods function expectedly
    """

    def setUp(self) -> None:
        """
        Setup for tests
        """
        super().setUp()

        self.query = MagicMock()
        self.instance = ServerManager(cloud_account="test_account")

        # pylint:disable=protected-access
        self.instance._query = self.query

        # to add future tests
