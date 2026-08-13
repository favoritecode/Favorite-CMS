import pytest

from backend.core import Kernel
from backend.engines.settings import (
    ProtectedSettingValue, SettingDefinition, SettingScope, SettingScopeKind, SettingsEngine,
)
from backend.engines.settings.engine import InvalidSetting
from backend.engines.permissions import PermissionDenied
from backend.tests.platform_data.conftest import authenticated, permission


def test_settings_defaults_update_reset_and_scope_isolation(data_kernel: Kernel) -> None:
    engine = data_kernel.container.resolve("engine.settings", SettingsEngine)
    engine.register(SettingDefinition("tests.enabled", "tests", SettingScopeKind.PLUGIN, bool, default=False))
    one = SettingScope(SettingScopeKind.PLUGIN, "tests", "one"); two = SettingScope(SettingScopeKind.PLUGIN, "tests", "two")
    assert engine.get("tests.enabled", one).value is False
    assert engine.set("tests.enabled", one, True).value is True
    assert engine.get("tests.enabled", two).value is False
    assert engine.reset("tests.enabled", one).value is False
    with pytest.raises(InvalidSetting): engine.set("tests.enabled", one, "yes")


def test_sensitive_setting_requires_authorization_and_redacts(data_kernel: Kernel) -> None:
    permission(data_kernel, "tests.setting.read", "read", "setting", allow_owner=True)
    permission(data_kernel, "tests.setting.update", "update", "setting", allow_owner=True)
    auth = authenticated(data_kernel); assert auth.user_id is not None
    engine = data_kernel.container.resolve("engine.settings", SettingsEngine)
    engine.register(SettingDefinition("tests.private", "tests", SettingScopeKind.USER, str, default="hidden",
                                      sensitive=True, read_permission="tests.setting.read", write_permission="tests.setting.update"))
    scope = SettingScope(SettingScopeKind.USER, "tests", auth.user_id)
    with pytest.raises(PermissionDenied): engine.get("tests.private", scope)
    result = engine.set("tests.private", scope, "new-secret", auth)
    assert isinstance(result.value, ProtectedSettingValue) and str(result.value) == "[REDACTED]"
    assert "new-secret" not in repr(result.value)
