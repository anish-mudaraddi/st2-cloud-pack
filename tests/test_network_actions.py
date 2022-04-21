from unittest.mock import create_autospec, NonCallableMock

from enums.rbac_network_actions import RbacNetworkActions
from openstack_network import OpenstackNetwork
from src.network_actions import NetworkActions
from tests.openstack_action_test_case import OpenstackActionTestCase


class TestNetworkActions(OpenstackActionTestCase):
    """
    Unit tests for the Network.* actions
    """

    action_cls = NetworkActions

    def setUp(self):
        super().setUp()
        self.network_mock = create_autospec(OpenstackNetwork)
        self.action: NetworkActions = self.get_action_instance(
            api_mock=self.network_mock
        )

    def test_find_network_found(self):
        returned = self.action.network_find(NonCallableMock(), NonCallableMock())
        expected = self.network_mock.find_network.return_value
        assert returned == (True, expected)

    def test_find_network_not_found(self):
        self.network_mock.find_network.return_value = None
        returned = self.action.network_find(NonCallableMock(), NonCallableMock())
        assert returned[0] is False
        assert "could not be found" in returned[1]

    def test_create_rbac_successful(self):
        for action in ["external", "shared"]:
            returned = self.action.network_rbac_create(
                NonCallableMock(), NonCallableMock(), NonCallableMock(), action
            )
            expected = self.network_mock.create_network_rbac.return_value
            assert returned == (True, expected)

    def test_create_rbac_failed(self):
        self.network_mock.create_network_rbac.return_value = None
        returned = self.action.network_rbac_create(
            NonCallableMock(),
            NonCallableMock(),
            NonCallableMock(),
            RbacNetworkActions.SHARED.value,
        )
        assert returned == (False, None)
