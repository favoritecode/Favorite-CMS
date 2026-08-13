from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.core.extensions import ExtensionManifest, ExtensionState, ManifestValidationError
from backend.engines.api import APIEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.permissions import PermissionEngine, RoleGrant
from backend.engines.plugins import PluginEngine
from backend.engines.plugins.reference import load_reference_runtime
from backend.engines.rendering import RenderingEngine
from backend.engines.routing import RouteNotFound, RoutingEngine
from backend.engines.users import UserEngine
from backend.engines.themes import ThemeEngine
from backend.tests.phase7.conftest import phase7_kernel
from backend.bootstrap import build_kernel
from backend.database.migrations import DatabaseMigrationEngine

PLUGIN_ID = "favorite.plugin.example"
CAPABILITIES = frozenset({"admin.register", "api.register", "rendering.register", "routing.register", "settings.access"})


def _credential(kernel) -> str:
    users = kernel.container.resolve("engine.users", UserEngine)
    authentication = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    user = users.create(email="plugin@example.test", display_name="Plugin Operator", role="plugin-operator")
    authentication.set_password(user.user_id, "a sufficiently long plugin password")
    permissions.grant_role(RoleGrant("plugin-operator", "admin.extensions.manage", "application.admin.platform"))
    result = authentication.login(email="plugin@example.test", password="a sufficiently long plugin password")
    assert result.token is not None
    return result.token.reveal()


def test_reference_package_discovery_validation_permissions_lifecycle_and_state(phase7_kernel) -> None:
    assert phase7_kernel.container.resolve("engine.themes", ThemeEngine).activate("favorite.theme.starter")
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    api = phase7_kernel.container.resolve("engine.api", APIEngine)
    rendering = phase7_kernel.container.resolve("engine.rendering", RenderingEngine)
    manager = phase7_kernel.extensions
    manifest = plugins.manifest(PLUGIN_ID)
    assert manifest.version == "1.0.0" and frozenset(manifest.permissions) == CAPABILITIES
    with pytest.raises(ManifestValidationError):
        plugins.bind_declarative(PLUGIN_ID, granted_permissions=frozenset())
    plugins.bind_declarative(PLUGIN_ID, granted_permissions=CAPABILITIES)
    assert plugins.activate(PLUGIN_ID)
    credential = _credential(phase7_kernel)
    route = routing.resolve("PATCH", "/api/plugins/example")
    assert api.handle(route, body={"message": "State survives lifecycle restarts."}, credential=credential).status == 200
    public = rendering.render(routing.resolve("GET", "/plugins/example"))
    assert public.status == 200 and "State survives lifecycle restarts." in public.body
    assert plugins.deactivate(PLUGIN_ID)
    for method, path in (("GET", "/api/plugins/example"), ("GET", "/plugins/example")):
        with pytest.raises(RouteNotFound): routing.resolve(method, path)
    assert plugins.activate(PLUGIN_ID)
    response = api.handle(routing.resolve("GET", "/api/plugins/example"), credential=credential)
    assert response.status == 200 and response.body["data"]["message"] == "State survives lifecycle restarts."


def test_failed_reference_update_rolls_back_active_runtime(tmp_path: Path, phase7_kernel) -> None:
    assert phase7_kernel.container.resolve("engine.themes", ThemeEngine).activate("favorite.theme.starter")
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    plugins.bind_declarative(PLUGIN_ID, granted_permissions=CAPABILITIES)
    assert plugins.activate(PLUGIN_ID)
    package = tmp_path / "candidate"; package.mkdir()
    (package / "contributions.json").write_text(json.dumps({"schemaVersion": 1, "kind": "reference-message",
        "title": "Broken candidate", "defaultMessage": "Never active", "activation": "fail"}), encoding="utf-8")
    runtime = load_reference_runtime(package, PLUGIN_ID)
    raw = json.loads(Path("plugins/favorite.plugin.example/plugin.json").read_text(encoding="utf-8")); raw["version"] = "1.1.0"
    assert not plugins.update(PLUGIN_ID, ExtensionManifest.from_mapping(raw), runtime, granted_permissions=CAPABILITIES)
    assert phase7_kernel.extensions.state(PLUGIN_ID) is ExtensionState.ENABLED
    response = phase7_kernel.container.resolve("engine.rendering", RenderingEngine).render(
        phase7_kernel.container.resolve("engine.routing", RoutingEngine).resolve("GET", "/plugins/example"))
    assert response.status == 200 and "Example Plugin" in response.body and "Broken candidate" not in response.body


def test_reference_package_is_data_only_and_has_no_private_infrastructure_access() -> None:
    package_files = tuple(path.name for path in Path("plugins/favorite.plugin.example").iterdir())
    assert set(package_files) == {"plugin.json", "contributions.json", "README.md"}
    source = Path("backend/engines/plugins/reference.py").read_text(encoding="utf-8")
    for prohibited in ("sqlalchemy", "os.getenv", "subprocess", "os.system", "importlib", "eval(", "exec(", "StorageProvider", "DatabaseEngine"):
        assert prohibited not in source


def test_plugin_scoped_state_survives_kernel_restart(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'restart.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "plugin-restart-signing-key-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")
    first = build_kernel(); first.bootstrap()
    migrations = first.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade()
    credential = _credential(first); plugins = first.container.resolve("engine.plugins", PluginEngine)
    plugins.bind_declarative(PLUGIN_ID, granted_permissions=CAPABILITIES); assert plugins.activate(PLUGIN_ID)
    api = first.container.resolve("engine.api", APIEngine); routing = first.container.resolve("engine.routing", RoutingEngine)
    assert api.handle(routing.resolve("PATCH", "/api/plugins/example"), body={"message": "Durable Plugin state."}, credential=credential).status == 200
    first.shutdown()
    second = build_kernel(); second.bootstrap()
    try:
        migrations = second.container.resolve("engine.migrations", DatabaseMigrationEngine)
        migrations.initialize_history(); migrations.upgrade()
        auth = second.container.resolve("engine.authentication", AuthenticationEngine).login(
            email="plugin@example.test", password="a sufficiently long plugin password")
        assert auth.token is not None
        plugins = second.container.resolve("engine.plugins", PluginEngine)
        plugins.bind_declarative(PLUGIN_ID, granted_permissions=CAPABILITIES); assert plugins.activate(PLUGIN_ID)
        response = second.container.resolve("engine.api", APIEngine).handle(
            second.container.resolve("engine.routing", RoutingEngine).resolve("GET", "/api/plugins/example"),
            credential=auth.token.reveal())
        assert response.status == 200 and response.body["data"]["message"] == "Durable Plugin state."
    finally: second.shutdown()
