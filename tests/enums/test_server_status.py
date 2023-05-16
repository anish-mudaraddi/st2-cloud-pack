from parameterized import parameterized

from enums.user_domains import ServerStatus


@parameterized(["SUSPENDED", "SuspendeD", "suspended"])
def test_suspended_status_serialization(val):
    """
    Tests that variants of SUSPENDED status can be serialized
    """
    assert ServerStatus.from_string(val) is ServerStatus.SUSPENDED


@parameterized(["ACTIVE", "AcTiVE", "active"])
def test_active_status_serialization(val):
    """
    Tests that variants of ACTIVE status can be serialized
    """
    assert ServerStatus.from_string(val) is ServerStatus.ACTIVE


@parameterized(["SHUTOFF", "ShutOff", "shutoff"])
def test_shutoff_status_serialization(val):
    """
    Tests that variants of SHUTOFF status can be serialized
    """
    assert ServerStatus.from_string(val) is ServerStatus.SHUTOFF


@parameterized(["ERROR", "ErRor", "error"])
def test_error_status_serialization(val):
    """
    Tests that variants of ERROR status can be serialized
    """
    assert ServerStatus.from_string(val) is ServerStatus.ERROR
