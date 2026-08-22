import json
from pathlib import Path

import pytest

from backend.bootstrap import build_kernel
from backend.core.extensions import ExtensionState, ManifestValidationError
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.permissions import PermissionEngine
from backend.engines.plugins import PluginEngine
from backend.engines.tools import ToolEngine


PLUGINS = {
    "favorite.plugin.ocr": "favorite.tool.ocr",
    "favorite.plugin.direct-media": "favorite.tool.direct-media-download",
}
CAPABILITIES = frozenset({"permission.register", "tool.register"})


@pytest.fixture
def phase7_kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'tools-plugins.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "tool-plugin-test-signing-key-at-least-thirty-two-bytes")
    kernel = build_kernel()
    kernel.bootstrap()
    migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history()
    migrations.upgrade()
    try:
        yield kernel
    finally:
        kernel.shutdown()


def test_bundled_tool_plugins_are_declarative_inactive_and_capability_gated(phase7_kernel) -> None:
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    tools = phase7_kernel.container.resolve("engine.tools", ToolEngine)
    permissions = phase7_kernel.container.resolve("engine.permissions", PermissionEngine)

    for plugin_id, tool_id in PLUGINS.items():
        manifest = plugins.manifest(plugin_id)
        assert manifest.version == "1.0.0"
        assert frozenset(manifest.permissions) == CAPABILITIES
        assert phase7_kernel.extensions.state(plugin_id) is ExtensionState.INSTALLED
        with pytest.raises(ManifestValidationError, match="permissions were not granted"):
            plugins.bind_declarative(plugin_id, granted_permissions=frozenset())

        plugins.bind_declarative(plugin_id, granted_permissions=CAPABILITIES)
        assert plugins.activate(plugin_id)
        contract = next(item for item in tools.contracts(plugin_id) if item.tool_id == tool_id)
        assert contract.public is False
        definition = next(item for item in permissions.definitions() if item.permission_id == contract.execute_permission)
        assert definition.owner == plugin_id
        assert plugins.deactivate(plugin_id)
        assert tools.contracts(plugin_id) == ()


def test_bundled_tool_packages_do_not_select_executable_code_or_services() -> None:
    for plugin_id in PLUGINS:
        root = Path("plugins") / plugin_id
        assert {path.name for path in root.iterdir()} == {"README.md", "contributions.json", "plugin.json"}
        contribution = json.loads((root / "contributions.json").read_text(encoding="utf-8"))
        serialized = json.dumps(contribution).casefold()
        for prohibited in ("module", "callable", "command", "environment", "database", "storage_provider"):
            assert prohibited not in serialized
