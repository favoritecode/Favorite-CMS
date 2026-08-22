from __future__ import annotations

from io import BytesIO
import base64
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import pytest

from backend.bootstrap import build_kernel
from backend.core import Kernel
from backend.core.extensions import ExtensionState, ExtensionType
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.api import APIEngine
from backend.engines.audit import AuditEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.extension_packages import ExtensionPackageEngine, PackageError
from backend.engines.permissions import PermissionEngine
from backend.engines.plugins import PluginEngine
from backend.engines.routing import RoutingEngine
from backend.engines.rendering import RenderingEngine
from backend.engines.users import AccountState, UserEngine


@pytest.fixture
def management_kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'management.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "management-test-signing-key-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")
    first = build_kernel(); first.bootstrap()
    migrations = first.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade(); first.shutdown()
    kernel = build_kernel(); kernel.bootstrap()
    yield kernel
    kernel.shutdown()


def _login(kernel: Kernel, *, role: str, email: str) -> str:
    users = kernel.container.resolve("engine.users", UserEngine)
    authentication = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    user = users.create(email=email, display_name=email.split("@")[0], role=role)
    authentication.set_password(user.user_id, "correct horse battery staple")
    result = authentication.login(email=email, password="correct horse battery staple")
    assert result.success and result.token is not None
    return result.token.reveal()


def _request(kernel: Kernel, method: str, path: str, token: str, body=None):
    route = kernel.container.resolve("engine.routing", RoutingEngine).resolve(method, path)
    return kernel.container.resolve("engine.api", APIEngine).handle(route, body=body, credential=token)


def _manifest(identifier: str, kind: str, version: str = "1.0.0") -> dict[str, object]:
    return {"id": identifier, "type": kind, "name": "Uploaded extension", "version": version,
            "description": "A validated test package", "author": "Favorite CMS", "license": "MIT",
            "homepage": "https://example.invalid", "repository": "https://example.invalid/source",
            "minimumCoreVersion": "0.1.0", "maximumCoreVersion": "0.1.0",
            "dependencies": {}, "optionalDependencies": {}, "permissions": []}


def _zip(files: dict[str, bytes | str]) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        for name, value in files.items(): archive.writestr(name, value)
    return output.getvalue()


def _theme(identifier: str, version: str = "1.0.0", *, minimum_core: str = "0.1.0", maximum_core: str = "0.1.0") -> bytes:
    catalogue = {"templates": ["templates/page.html"], "layouts": ["layouts/base.html"],
                 "components": ["components/header.html", "components/footer.html"], "widgets": [], "assets": ["assets/starter.css"]}
    manifest = _manifest(identifier, "theme", version)
    manifest["minimumCoreVersion"] = minimum_core
    manifest["maximumCoreVersion"] = maximum_core
    return _zip({"theme.json": json.dumps(manifest),
                 "resources.json": json.dumps(catalogue), "templates/page.html": "<main>{{ header }}{{ content }}{{ footer }}</main>",
                 "layouts/base.html": "<html><style>{{ styles }}</style><body>{{ body }}</body></html>",
                 "components/header.html": "<header>Uploaded</header>", "components/footer.html": "<footer>Footer</footer>",
                 "assets/starter.css": "body{font-family:sans-serif}"})


def _plugin(identifier: str, version: str = "1.0.0") -> bytes:
    return _zip({"plugin.json": json.dumps(_manifest(identifier, "plugin", version)),
                 "contributions.json": json.dumps({"contributions": []})})


def test_site_owner_is_explicit_and_user_role_management_is_authorized(management_kernel: Kernel) -> None:
    permissions = management_kernel.container.resolve("engine.permissions", PermissionEngine)
    explicit = permissions.role_permissions("site-owner")
    assert "platform.user.create" in explicit and "platform.role.assign_permissions" in explicit
    assert len(explicit) < 100 and all(item in {definition.permission_id for definition in permissions.definitions()} for item in explicit)
    owner = _login(management_kernel, role="site-owner", email="owner@example.com")
    denied = _login(management_kernel, role="limited", email="limited@example.com")
    response = _request(management_kernel, "POST", "/admin/api/users", owner, {"action": "create", "email": "editor@example.com", "display_name": "Editor", "roles": ["admin"], "password": "another correct password"})
    assert response.status == 200 and response.body["data"]["email"] == "editor@example.com"
    forbidden = _request(management_kernel, "POST", "/admin/api/users", denied, {"action": "disable", "id": response.body["data"]["id"]})
    assert forbidden.status == 403
    role = _request(management_kernel, "POST", "/admin/api/roles", owner, {"action": "create", "id": "content-editor", "name": "Content Editor"})
    assert role.status == 200 and not role.body["data"]["built_in"]
    changed = _request(management_kernel, "POST", "/admin/api/roles", owner, {"action": "permissions", "id": "content-editor", "permissions": ["platform.content.read"]})
    assert changed.status == 200 and changed.body["data"]["permissions"] == ["platform.content.read"]
    audit = management_kernel.container.resolve("engine.audit", AuditEngine).recent()
    assert {record.action for record in audit} >= {"user.create", "role.create", "role.permissions"}
    assert "password" not in repr(audit).casefold() and "editor@example.com" not in repr(audit)


def test_credential_and_site_owner_lockout_guards_are_backend_enforced(management_kernel: Kernel) -> None:
    owner = _login(management_kernel, role="site-owner", email="guarded-owner@example.com")
    users = management_kernel.container.resolve("engine.users", UserEngine)
    owner_user = users.find_by_email("guarded-owner@example.com")
    assert owner_user is not None
    short = _request(management_kernel, "POST", "/admin/api/users", owner,
        {"action": "create", "email": "orphan@example.com", "display_name": "Orphan", "roles": ["admin"], "password": "short"})
    assert short.status == 400 and users.find_by_email("orphan@example.com") is None
    disabled = _request(management_kernel, "POST", "/admin/api/users", owner, {"action": "disable", "id": owner_user.user_id})
    assert disabled.status == 400 and users.get(owner_user.user_id).state is AccountState.ACTIVE
    removed = _request(management_kernel, "POST", "/admin/api/users", owner,
        {"action": "assign_roles", "id": owner_user.user_id, "roles": ["admin"]})
    assert removed.status == 400 and "site-owner" in users.get(owner_user.user_id).roles
    built_in = _request(management_kernel, "POST", "/admin/api/roles", owner,
        {"action": "permissions", "id": "site-owner", "permissions": ["platform.content.read"]})
    assert built_in.status == 400


def test_theme_and_plugin_zip_lifecycle_is_storage_backed_and_inactive(management_kernel: Kernel) -> None:
    packages = management_kernel.container.resolve("engine.extension_packages", ExtensionPackageEngine)
    theme = packages.install(_theme("example.theme.uploaded"), expected_type=ExtensionType.THEME)
    plugin = packages.install(_plugin("example.plugin.uploaded"), expected_type=ExtensionType.PLUGIN)
    assert theme.action == plugin.action == "installed"
    assert management_kernel.extensions.state(theme.extension_id) is ExtensionState.INSTALLED
    assert management_kernel.extensions.state(plugin.extension_id) is ExtensionState.INSTALLED
    plugins = management_kernel.container.resolve("engine.plugins")
    plugins.bind_uploaded_declarative(plugin.extension_id, granted_permissions=frozenset())
    assert plugins.activate(plugin.extension_id)
    assert plugins.deactivate(plugin.extension_id)
    packages.uninstall(plugin.extension_id)
    assert plugin.extension_id not in management_kernel.extensions.registered()


def test_archive_security_and_update_rollback(management_kernel: Kernel) -> None:
    packages = management_kernel.container.resolve("engine.extension_packages", ExtensionPackageEngine)
    with pytest.raises(PackageError, match="malformed"): packages.install(b"not a zip", expected_type=ExtensionType.THEME)
    with pytest.raises(PackageError, match="unsafe path"): packages.install(_zip({"../theme.json": "{}"}), expected_type=ExtensionType.THEME)
    with pytest.raises(PackageError, match="unsafe path"): packages.install(_zip({"C:/theme.json": "{}"}), expected_type=ExtensionType.THEME)
    with pytest.raises(PackageError, match="manifest"): packages.install(_zip({"theme.json": "not-json"}), expected_type=ExtensionType.THEME)
    with pytest.raises(PackageError, match="compatible"):
        packages.install(_theme("example.theme.incompatible", minimum_core="9.0.0", maximum_core="10.0.0"), expected_type=ExtensionType.THEME)
    oversized = _manifest("example.theme.oversized", "theme")
    with pytest.raises(PackageError, match="limit"):
        packages.install(_zip({"theme.json": json.dumps(oversized), "padding.txt": b"x" * (5 * 1024 * 1024)}), expected_type=ExtensionType.THEME)
    link = BytesIO()
    with ZipFile(link, "w") as archive:
        info = ZipInfo("theme.json"); info.external_attr = 0o120777 << 16; archive.writestr(info, "target")
    with pytest.raises(PackageError, match="link"): packages.install(link.getvalue(), expected_type=ExtensionType.THEME)
    installed = packages.install(_theme("example.theme.rollback"), expected_type=ExtensionType.THEME)
    with pytest.raises(PackageError, match="identifier"): packages.update(installed.extension_id, _theme("other.theme.rollback", "2.0.0"))
    assert management_kernel.extensions.manifest(installed.extension_id).version == "1.0.0"
    updated = packages.update(installed.extension_id, _theme(installed.extension_id, "2.0.0"))
    assert updated.version == "2.0.0"
    with pytest.raises(PackageError, match="executable"):
        packages.install(_zip({"plugin.json": json.dumps(_manifest("example.plugin.unsafe", "plugin")), "code.py": "print('unsafe')"}), expected_type=ExtensionType.PLUGIN)
    unsafe_theme = _theme("example.theme.scripted")
    with ZipFile(BytesIO(unsafe_theme)) as source:
        unsafe_files = {name: source.read(name) for name in source.namelist()}
    unsafe_files["templates/page.html"] = "<main><script>alert(1)</script></main>"
    with pytest.raises(PackageError, match="executable browser"):
        packages.install(_zip(unsafe_files), expected_type=ExtensionType.THEME)


def test_real_admin_extension_api_installs_inactive_and_switches_rendering(management_kernel: Kernel) -> None:
    owner = _login(management_kernel, role="site-owner", email="package-owner@example.com")
    identifier = "example.theme.api"
    installed = _request(management_kernel, "POST", "/admin/api/extensions", owner,
        {"type": "theme", "action": "install", "archive": base64.b64encode(_theme(identifier)).decode("ascii")})
    assert installed.status == 200 and management_kernel.extensions.state(identifier) is ExtensionState.INSTALLED
    values = {item["id"]: item for item in installed.body["data"]}
    assert values[identifier]["package_managed"] is True
    assert values["favorite.theme.starter"]["package_managed"] is False
    denied = _login(management_kernel, role="limited", email="package-denied@example.com")
    forbidden = _request(management_kernel, "POST", "/admin/api/extensions", denied,
        {"type": "plugin", "action": "install", "archive": base64.b64encode(_plugin("example.plugin.denied")).decode("ascii")})
    assert forbidden.status == 403
    activated = _request(management_kernel, "POST", "/admin/api/extensions", owner,
        {"type": "theme", "id": identifier, "action": "activate"})
    assert activated.status == 200
    route = management_kernel.container.resolve("engine.routing", RoutingEngine).resolve("GET", "/site/welcome")
    rendered = management_kernel.container.resolve("engine.rendering", RenderingEngine).render(route)
    assert rendered.status == 200 and "Uploaded" in rendered.body
    active_uninstall = _request(management_kernel, "POST", "/admin/api/extensions", owner,
        {"type": "theme", "id": identifier, "action": "uninstall"})
    assert active_uninstall.status == 400
    assert management_kernel.extensions.state(identifier) is ExtensionState.ENABLED
    restored = _request(management_kernel, "POST", "/admin/api/extensions", owner,
        {"type": "theme", "id": "favorite.theme.starter", "action": "activate"})
    assert restored.status == 200


def test_uploaded_plugin_installation_and_active_state_restore_after_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test"); monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'restart.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage")); monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "restart-signing-key-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")
    initial = build_kernel(); initial.bootstrap(); migrations = initial.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade(); initial.shutdown()
    first = build_kernel(); first.bootstrap(); packages = first.container.resolve("engine.extension_packages", ExtensionPackageEngine)
    result = packages.install(_plugin("example.plugin.restart"), expected_type=ExtensionType.PLUGIN)
    plugins = first.container.resolve("engine.plugins", PluginEngine); plugins.bind_uploaded_declarative(result.extension_id, granted_permissions=frozenset())
    assert plugins.activate(result.extension_id)
    packages.set_lifecycle(result.extension_id, extension_type=ExtensionType.PLUGIN, active=True)
    first.shutdown()
    second = build_kernel(); second.bootstrap()
    try: assert second.extensions.state(result.extension_id) is ExtensionState.ENABLED
    finally: second.shutdown()
