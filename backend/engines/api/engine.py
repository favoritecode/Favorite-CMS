"""HTTP/API coordination over Route Context; this module owns no route registry."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping
from uuid import uuid4

from backend.core.container import ServiceContainer
from backend.engines.authentication import AuthenticationContext, AuthenticationEngine
from backend.engines.errors import ApplicationFailure, ErrorCategory, ErrorHandlingEngine, ValidationFailure
from backend.engines.permissions import AuthorizationContext, PermissionDenied, PermissionEngine
from backend.engines.routing import RouteContext, RouteDefinition, RouteType, RoutingEngine
from backend.engines.plugins import PluginEngine
from backend.engines.authentication import CredentialToken

class APIValidationError(ValidationFailure): pass
class APIAuthenticationRequired(ApplicationFailure): pass
class APIResourceNotFound(ApplicationFailure): pass
class APIConflict(ApplicationFailure): pass

@dataclass(frozen=True)
class APIAccessCredential:
    access_token: CredentialToken

@dataclass(frozen=True)
class APIRequest:
    request_id: str
    route: RouteContext
    query: Mapping[str, str]
    body: object
    headers: Mapping[str, str]
    authentication: AuthenticationContext

@dataclass(frozen=True)
class APIResponse:
    status: int
    body: Mapping[str, object]
    headers: Mapping[str, str] = MappingProxyType({"content-type": "application/json"})

Validator = Callable[[Mapping[str, str], object], object]
Handler = Callable[[APIRequest, object], object]
Serializer = Callable[[object], object]
AuthorizationFactory = Callable[[APIRequest], AuthorizationContext]

@dataclass(frozen=True)
class APIOperation:
    target: str
    owner: str
    validator: Validator
    handler: Handler
    serializer: Serializer
    success_status: int = 200
    authorization: AuthorizationFactory | None = None
    contract_version: str = "1"
    def __post_init__(self) -> None:
        if not self.target.strip() or not self.owner.strip() or not self.contract_version.strip():
            raise APIValidationError("API operation contract is invalid")
        if self.success_status < 200 or self.success_status > 299:
            raise APIValidationError("API success status is invalid")

class APIEngine:
    engine_id = "api"
    dependencies = ("routing", "authentication", "permissions")
    def __init__(self) -> None:
        self._routing: RoutingEngine | None = None; self._authentication: AuthenticationEngine | None = None
        self._permissions: PermissionEngine | None = None; self._errors: ErrorHandlingEngine | None = None
        self._operations: dict[str, APIOperation] = {}; self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._routing = container.resolve("engine.routing", RoutingEngine)
        self._authentication = container.resolve("engine.authentication", AuthenticationEngine)
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        self._errors = container.resolve("core.errors", ErrorHandlingEngine)
        container.register("engine.api", self)
        container.resolve("engine.plugins", PluginEngine).publish_phase_service("engine.api", self)
    def start(self) -> None:
        self.register(
            RouteDefinition("platform.api.status", "engine.api", RouteType.API, "/", ("GET",), "platform.api.status"),
            APIOperation("platform.api.status", "engine.api", _empty_request,
                         lambda request, validated: {"name": "Favorite CMS", "status": "ready"}, lambda value: value),
        )
        self.ready = True
    def shutdown(self) -> None: self.ready = False; self._operations.clear()
    def register(self, route: RouteDefinition, operation: APIOperation) -> None:
        if route.route_type is not RouteType.API or route.target != operation.target or route.owner != operation.owner:
            raise APIValidationError("API Route and operation contracts do not agree")
        if route.permission is not None and operation.authorization is None:
            raise APIValidationError("Protected API operation requires an authorization context contract")
        if operation.target in self._operations: raise APIConflict("API operation is already registered")
        self._routing_required().register(route)
        self._operations[operation.target] = operation
    def unregister(self, target: str, *, owner: str) -> None:
        operation = self._operations.get(target)
        if operation is None or operation.owner != owner: raise APIResourceNotFound("API operation is unavailable")
        routes = [route for route in self._routing_required().discover() if route.target == target]
        for route in routes: self._routing_required().unregister(route.route_id, owner=owner)
        del self._operations[target]
    def unregister_owner(self, owner: str) -> None:
        for target in tuple(self._operations):
            if self._operations[target].owner == owner:
                self.unregister(target, owner=owner)
    def for_plugin(self, plugin_id: str) -> "PluginAPI": return PluginAPI(self, plugin_id)
    def handle(self, route: RouteContext, *, query: Mapping[str, str] | None = None,
               body: object = None, headers: Mapping[str, str] | None = None,
               credential: str | None = None, request_id: str | None = None) -> APIResponse:
        request_id = request_id or str(uuid4())
        try:
            if route.route_type is not RouteType.API: raise APIValidationError("Route is not an API Route")
            operation = self._operations.get(route.target)
            if operation is None or operation.owner != route.owner: raise APIResourceNotFound("API operation is unavailable")
            authentication = self._authentication_required().resolve(credential)
            if route.authentication_required and not authentication.authenticated:
                raise APIAuthenticationRequired("Authentication is required")
            safe_headers = {key.lower(): value for key, value in (headers or {}).items() if key.lower() in {"content-type", "accept", "x-request-id"}}
            request = APIRequest(request_id, route, MappingProxyType(dict(query or {})), body,
                                 MappingProxyType(safe_headers), authentication)
            validated = operation.validator(request.query, body)
            if route.permission is not None:
                assert operation.authorization is not None
                self._permissions_required().require(route.permission, operation.authorization(request))
            result = operation.handler(request, validated)
            payload = _public_value(operation.serializer(result))
            return APIResponse(operation.success_status, MappingProxyType({"success": True, "data": payload, "request_id": request_id}))
        except Exception as exc:
            return self._error_response(exc, request_id)
    def invalid_request(self, message: str, *, request_id: str) -> APIResponse:
        return self._error_response(APIValidationError(message), request_id)
    def _error_response(self, exc: Exception, request_id: str) -> APIResponse:
        record = self._errors_required().normalize(exc, source="engine.api", context={"request_id": request_id})
        if isinstance(exc, APIAuthenticationRequired): status, code = 401, "authentication_required"
        elif isinstance(exc, PermissionDenied): status, code = 403, "permission_denied"
        elif isinstance(exc, APIResourceNotFound): status, code = 404, "resource_unavailable"
        elif isinstance(exc, APIConflict): status, code = 409, "conflict"
        elif record.category is ErrorCategory.VALIDATION: status, code = 400, "validation_error"
        elif record.category is ErrorCategory.APPLICATION: status, code = 422, "operation_failed"
        elif record.category is ErrorCategory.INFRASTRUCTURE: status, code = 503, "service_unavailable"
        else: status, code = 500, "internal_error"
        return APIResponse(status, MappingProxyType({"success": False, "error": {"code": code, "message": record.safe_message, "error_id": record.error_id}, "request_id": request_id}))
    def _routing_required(self) -> RoutingEngine:
        if self._routing is None: raise RuntimeError("API Engine is not initialized")
        return self._routing
    def _authentication_required(self) -> AuthenticationEngine:
        if self._authentication is None: raise RuntimeError("API Engine is not initialized")
        return self._authentication
    def _permissions_required(self) -> PermissionEngine:
        if self._permissions is None: raise RuntimeError("API Engine is not initialized")
        return self._permissions
    def _errors_required(self) -> ErrorHandlingEngine:
        if self._errors is None: raise RuntimeError("API Engine is not initialized")
        return self._errors

_SENSITIVE = ("password", "token", "secret", "credential", "hash", "storage_path", "filesystem")
def _public_value(value: object) -> object:
    if isinstance(value, APIAccessCredential):
        token = value.access_token
        if not isinstance(token, CredentialToken): raise APIValidationError("API credential response is invalid")
        return {"access_token": token.reveal(), "token_type": "Bearer"}
    if value is None or isinstance(value, (bool, int, float, str)): return value
    if isinstance(value, (list, tuple)): return [_public_value(item) for item in value]
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str) or any(part in key.lower() for part in _SENSITIVE):
                raise APIValidationError("API response contains a prohibited field")
            result[key] = _public_value(item)
        return result
    raise APIValidationError("API response contains an unsupported value")

def _empty_request(query: Mapping[str, str], body: object) -> object:
    if query or body is not None: raise APIValidationError("Request contains unsupported input")
    return None

class PluginAPI:
    def __init__(self, api: APIEngine, plugin_id: str) -> None: self._api = api; self._plugin_id = plugin_id
    def register(self, route: RouteDefinition, operation: APIOperation) -> None:
        if route.owner != self._plugin_id or operation.owner != self._plugin_id:
            raise APIValidationError("Plugin API owner is invalid")
        self._api.register(route, operation)
    def unregister(self, target: str) -> None: self._api.unregister(target, owner=self._plugin_id)
