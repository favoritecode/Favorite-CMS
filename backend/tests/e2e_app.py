"""Synthetic, local-only application fixture for real Playwright transport flows."""
from pathlib import Path

from backend.admin import AdminEngine, AdminModule
from backend.core import Kernel
from backend.core.extensions import ExtensionManifest, ExtensionManager
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.content import ContentEngine
from backend.engines.permissions import PermissionDefinition, PermissionEngine, RoleGrant
from backend.engines.plugins import PluginEngine
from backend.engines.search import SearchDocument, SearchEngine
from backend.engines.themes import ThemeEngine, ThemePackage
from backend.engines.users import UserEngine
from backend.main import create_app

OWNER = "application.admin.platform"
PASSWORD = "correct horse battery staple"

class _Runtime:
    def register(self, context=None): pass
    def activate(self): pass
    def deactivate(self): pass
    def unregister(self): pass
class _FailingRuntime(_Runtime):
    def activate(self): raise RuntimeError("synthetic activation failure")

def _manifest(identifier: str, kind: str) -> ExtensionManifest:
    return ExtensionManifest.from_mapping({"id": identifier, "type": kind, "name": identifier, "version": "1.0.0",
        "description": "Synthetic E2E extension", "author": "Favorite CMS", "license": "MIT",
        "homepage": "https://example.test", "repository": "https://example.test/repository",
        "minimumCoreVersion": "0.1.0", "maximumCoreVersion": "0.1.0", "dependencies": {},
        "optionalDependencies": {}, "permissions": []})


def seed(kernel: Kernel) -> None:
    migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade()
    users = kernel.container.resolve("engine.users", UserEngine)
    authentication = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    permissions.register(PermissionDefinition("tests.admin.view", "tests.e2e", "view", "admin_module"))
    permissions.grant_role(RoleGrant("e2e-operator", "tests.admin.view", "tests.e2e"))
    domain_permissions = tuple(f"platform.content.{action}" for action in ("create", "read", "update", "delete", "publish", "archive")) + tuple(
        f"platform.media.{action}" for action in ("create", "read", "update", "delete")) + ("platform.setting.read", "platform.setting.write")
    for permission_id in domain_permissions:
        permissions.grant_role(RoleGrant("e2e-operator", permission_id, OWNER))
    for permission_id in ("admin.content.manage", "admin.media.manage", "admin.settings.manage", "admin.extensions.manage", "admin.users.manage", "admin.roles.manage", "admin.diagnostics.view"):
        permissions.grant_role(RoleGrant("e2e-operator", permission_id, OWNER))
    for permission_id in tuple(f"platform.user.{action}" for action in ("create", "read", "update", "disable", "reset_password", "assign_roles")) + tuple(
        f"platform.role.{action}" for action in ("create", "read", "update", "delete", "assign_permissions")) + tuple(
        f"platform.extension.{action}" for action in ("install", "activate", "deactivate", "update", "uninstall")):
        permissions.grant_role(RoleGrant("e2e-operator", permission_id, OWNER))
    for email, role in (("operator@example.test", "e2e-operator"), ("viewer@example.test", "e2e-viewer")):
        user = users.find_by_email(email) or users.create(email=email, display_name="E2E User", role=role)
        authentication.set_password(user.user_id, PASSWORD)
    kernel.container.resolve("application.admin", AdminEngine).register_module(
        AdminModule("tests.admin.module", "tests.e2e", "Test management", "/admin/test-management",
                    "tests.admin.view", "view", "admin_module")
    )
    auth = authentication.login(email="operator@example.test", password=PASSWORD)
    assert auth.token is not None
    context = authentication.resolve(auth.token.reveal())
    content = kernel.container.resolve("engine.content", ContentEngine)
    page = content.create("page", title="Welcome to Favorite CMS", data={"slug": "welcome", "body": "Rendered by the backend presentation pipeline."}, metadata={}, authentication=context)
    content.publish(page.content_id, context)
    search = kernel.container.resolve("engine.search", SearchEngine)
    search.index(SearchDocument(page.content_id, "content", page.title, str(page.data["body"]), resource_reference=f"content:{page.content_id}"))
    manager = kernel.container.resolve("core.extensions", ExtensionManager)
    plugins = kernel.container.resolve("engine.plugins", PluginEngine)
    for identifier, runtime in (("tests.plugin.healthy", _Runtime()), ("tests.plugin.failing", _FailingRuntime())):
        manager.register(_manifest(identifier, "plugin")); plugins.bind(identifier, runtime)
    themes = kernel.container.resolve("engine.themes", ThemeEngine)
    root = Path(__file__).parent / "fixtures" / "theme"
    for identifier, runtime in (("tests.theme.failing", _FailingRuntime()),):
        manager.register(_manifest(identifier, "theme")); themes.bind(identifier, ThemePackage(root, templates=("page.html",)), runtime)


app = create_app(on_started=seed)
