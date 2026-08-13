"""Admin application contracts; Admin remains an API client, not a domain owner."""
from __future__ import annotations

from dataclasses import dataclass
import re

from backend.core.container import ServiceContainer
from backend.engines.api import APIAccessCredential, APIAuthenticationRequired, APIEngine, APIOperation, APIRequest, APIValidationError
from backend.engines.authentication import AuthenticationEngine, CredentialToken
from backend.engines.permissions import AuthorizationContext, PermissionEngine
from backend.engines.plugins import PluginEngine
from backend.engines.routing import RouteDefinition, RouteType

@dataclass(frozen=True)
class AdminModule:
    module_id: str
    owner: str
    label: str
    destination: str
    permission: str
    action: str
    resource_type: str
    order: int = 100
    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{2,127}", self.module_id): raise APIValidationError("Admin module identity is invalid")
        if not all(value.strip() for value in (self.owner, self.label, self.permission, self.action, self.resource_type)):
            raise APIValidationError("Admin module contract is invalid")
        if not self.destination.startswith("/admin/") or ".." in self.destination or "\\" in self.destination:
            raise APIValidationError("Admin module destination is invalid")

class AdminEngine:
    engine_id = "admin"
    dependencies = ("api", "users", "authentication", "permissions", "plugins", "themes")
    def __init__(self) -> None:
        self._api: APIEngine | None = None; self._authentication: AuthenticationEngine | None = None
        self._permissions: PermissionEngine | None = None; self._modules: dict[str, AdminModule] = {}; self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._api = container.resolve("engine.api", APIEngine); self._authentication = container.resolve("engine.authentication", AuthenticationEngine)
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        container.register("application.admin", self)
        container.resolve("engine.plugins", PluginEngine).publish_phase_service("application.admin", self)
    def start(self) -> None:
        api = self._api_required()
        api.register(RouteDefinition("admin.api.login", "application.admin", RouteType.API, "/admin/api/session", ("POST",), "admin.session.login"),
                     APIOperation("admin.session.login", "application.admin", _login_input, self._login, lambda value: value))
        api.register(RouteDefinition("admin.api.modules", "application.admin", RouteType.API, "/admin/api/modules", ("GET",), "admin.modules.list", authentication_required=True),
                     APIOperation("admin.modules.list", "application.admin", _empty_input, self._list_modules, lambda value: value))
        api.register(RouteDefinition("admin.api.logout", "application.admin", RouteType.API, "/admin/api/session", ("DELETE",), "admin.session.logout", authentication_required=True),
                     APIOperation("admin.session.logout", "application.admin", _empty_input, self._logout, lambda value: value))
        self.ready = True
    def shutdown(self) -> None: self.ready = False; self._modules.clear()
    def register_module(self, module: AdminModule) -> None:
        if module.module_id in self._modules: raise APIValidationError("Admin module is already registered")
        self._modules[module.module_id] = module
    def unregister_owner(self, owner: str) -> None:
        for identifier in tuple(self._modules):
            if self._modules[identifier].owner == owner: del self._modules[identifier]
    def for_plugin(self, plugin_id: str) -> "PluginAdmin": return PluginAdmin(self, plugin_id)
    def _login(self, request: APIRequest, data: object) -> APIAccessCredential:
        assert isinstance(data, dict)
        result = self._authentication_required().login(email=str(data["email"]), password=str(data["password"]))
        if not result.success or result.token is None: raise APIAuthenticationRequired("Authentication failed")
        return APIAccessCredential(result.token)
    def _list_modules(self, request: APIRequest, data: object) -> list[dict[str, object]]:
        visible = []
        for module in sorted(self._modules.values(), key=lambda item: (item.order, item.module_id)):
            decision = self._permissions_required().evaluate(module.permission, AuthorizationContext(module.action, module.resource_type, request.authentication))
            if decision.allowed:
                visible.append({"id": module.module_id, "label": module.label, "destination": module.destination, "owner": module.owner})
        return visible
    def _logout(self, request: APIRequest, data: object) -> dict[str, bool]:
        if not self._authentication_required().revoke_context(request.authentication):
            raise APIAuthenticationRequired("Authentication is required")
        return {"logged_out": True}
    def _api_required(self) -> APIEngine:
        if self._api is None: raise RuntimeError("Admin is not initialized")
        return self._api
    def _authentication_required(self) -> AuthenticationEngine:
        if self._authentication is None: raise RuntimeError("Admin is not initialized")
        return self._authentication
    def _permissions_required(self) -> PermissionEngine:
        if self._permissions is None: raise RuntimeError("Admin is not initialized")
        return self._permissions

class PluginAdmin:
    def __init__(self, admin: AdminEngine, plugin_id: str) -> None: self._admin = admin; self._plugin_id = plugin_id
    def register_module(self, module: AdminModule) -> None:
        if module.owner != self._plugin_id: raise APIValidationError("Plugin Admin module owner is invalid")
        self._admin.register_module(module)
    def unregister_all(self) -> None: self._admin.unregister_owner(self._plugin_id)

def _login_input(query, body):
    if query or not isinstance(body, dict) or set(body) != {"email", "password"}: raise APIValidationError("Login request is invalid")
    if not all(isinstance(body[key], str) and 0 < len(body[key]) <= 512 for key in body): raise APIValidationError("Login request is invalid")
    return body
def _empty_input(query, body):
    if query or body is not None: raise APIValidationError("Request contains unsupported input")
    return None
