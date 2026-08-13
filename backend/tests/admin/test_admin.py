from dataclasses import dataclass
import pytest
from backend.admin import AdminEngine, AdminModule, PluginAdmin
from backend.core import Kernel
from backend.core.extensions import ExtensionManifest
from backend.engines.api import APIEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.permissions import PermissionDefinition, PermissionEngine, RoleGrant
from backend.engines.plugins import PluginContext, PluginEngine
from backend.engines.routing import RoutingEngine
from backend.engines.users import AccountState, UserEngine
from backend.tests.extensions.conftest import manifest_data

def user_token(kernel: Kernel, *, state: AccountState = AccountState.ACTIVE) -> tuple[str, str]:
    users = kernel.container.resolve("engine.users", UserEngine); auth = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    user = users.create(email="admin@example.com", display_name="Administrator", role="manager")
    auth.set_password(user.user_id, "correct horse battery staple")
    if state is not AccountState.ACTIVE: users.set_state(user.user_id, state)
    result = auth.login(email=user.email, password="correct horse battery staple")
    return user.user_id, result.token.reveal() if result.token else ""

def test_login_uses_authentication_and_protects_credentials(phase7_kernel: Kernel) -> None:
    _, token = user_token(phase7_kernel)
    api = phase7_kernel.container.resolve("engine.api", APIEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    route = routing.resolve("POST", "/admin/api/session")
    invalid = api.handle(route, body={"email": "admin@example.com", "password": "wrong password"})
    assert invalid.status == 401 and "wrong password" not in str(invalid.body)
    valid = api.handle(route, body={"email": "admin@example.com", "password": "correct horse battery staple"})
    assert valid.status == 200 and phase7_kernel.container.resolve("engine.authentication", AuthenticationEngine).resolve(valid.body["data"]["access_token"]).authenticated
    assert "password" not in str(valid.body).lower()

def test_navigation_is_authenticated_and_permission_filtered(phase7_kernel: Kernel) -> None:
    _, token = user_token(phase7_kernel)
    permissions = phase7_kernel.container.resolve("engine.permissions", PermissionEngine)
    permissions.register(PermissionDefinition("content.manage", "engine.content", "manage", "content"))
    admin = phase7_kernel.container.resolve("application.admin", AdminEngine)
    admin.register_module(AdminModule("content.admin", "engine.content", "Content", "/admin/content", "content.manage", "manage", "content"))
    api = phase7_kernel.container.resolve("engine.api", APIEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    route = routing.resolve("GET", "/admin/api/modules")
    assert api.handle(route).status == 401
    denied = api.handle(route, credential=token)
    assert denied.status == 200 and denied.body["data"] == []
    permissions.grant_role(RoleGrant("manager", "content.manage", "engine.content"))
    allowed = api.handle(route, credential=token)
    assert allowed.body["data"] == [{"id": "content.admin", "label": "Content", "destination": "/admin/content", "owner": "engine.content"}]

def test_disabled_user_and_forged_token_are_denied(phase7_kernel: Kernel) -> None:
    user_id, token = user_token(phase7_kernel)
    users = phase7_kernel.container.resolve("engine.users", UserEngine)
    api = phase7_kernel.container.resolve("engine.api", APIEngine); route = phase7_kernel.container.resolve("engine.routing", RoutingEngine).resolve("GET", "/admin/api/modules")
    assert api.handle(route, credential="forged").status == 401
    users.change_state(user_id, AccountState.INACTIVE)
    assert api.handle(route, credential=token).status == 401

def test_logout_revokes_backend_credential(phase7_kernel: Kernel) -> None:
    _, token = user_token(phase7_kernel)
    api = phase7_kernel.container.resolve("engine.api", APIEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    response = api.handle(routing.resolve("DELETE", "/admin/api/session"), credential=token)
    assert response.status == 200 and response.body["data"] == {"logged_out": True}
    assert api.handle(routing.resolve("GET", "/admin/api/modules"), credential=token).status == 401

@dataclass
class AdminPlugin:
    context: PluginContext | None = None
    def register(self, context: PluginContext) -> None:
        self.context = context
        context.service("application.admin", PluginAdmin).register_module(AdminModule("plugin.admin.page", "favorite.plugin.admin", "Plugin", "/admin/plugin", "plugin.manage", "manage", "plugin"))
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass
    def unregister(self) -> None: pass

def test_plugin_admin_extension_is_owner_scoped_and_isolated(phase7_kernel: Kernel) -> None:
    manager = phase7_kernel.extensions; identifier = "favorite.plugin.admin"
    manager.register(ExtensionManifest.from_mapping(manifest_data(id=identifier)))
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine); runtime = AdminPlugin(); plugins.bind(identifier, runtime)
    assert plugins.activate(identifier)
    admin = phase7_kernel.container.resolve("application.admin", AdminEngine)
    assert "plugin.admin.page" in admin._modules
    assert plugins.deactivate(identifier)
    assert "plugin.admin.page" not in admin._modules

def test_invalid_admin_destination_and_duplicate_module_fail_closed(phase7_kernel: Kernel) -> None:
    with pytest.raises(Exception): AdminModule("bad.module", "tests", "Bad", "https://evil.example", "bad.manage", "manage", "bad")
    admin = phase7_kernel.container.resolve("application.admin", AdminEngine)
    module = AdminModule("tests.admin.module", "tests", "Test", "/admin/test", "tests.manage", "manage", "test")
    admin.register_module(module)
    with pytest.raises(Exception): admin.register_module(module)
