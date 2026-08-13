from backend.core import Kernel
from backend.engines.api import APIEngine, APIOperation, APIValidationError
from backend.engines.authentication import AuthenticationEngine
from backend.engines.permissions import AuthorizationContext, PermissionDefinition, PermissionEngine, RoleGrant
from backend.engines.routing import RouteDefinition, RouteType, RoutingEngine
from backend.engines.users import UserEngine

def register(api: APIEngine, route_id: str, target: str, handler, *, protected: bool = False) -> RouteDefinition:
    route = RouteDefinition(route_id, "engine.content", RouteType.API, "/" + route_id.replace(".", "/"), ("POST",), target,
                            authentication_required=protected, permission="content.read" if protected else None)
    authorization = (lambda request: AuthorizationContext("read", "content", request.authentication)) if protected else None
    api.register(route, APIOperation(target, "engine.content", lambda query, body: body if isinstance(body, dict) else (_ for _ in ()).throw(APIValidationError("Body must be an object")), handler, lambda value: value, authorization=authorization))
    return route

def test_validation_normalization_and_secret_filtering(phase7_kernel: Kernel) -> None:
    api = phase7_kernel.container.resolve("engine.api", APIEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    route = register(api, "tests.api.echo", "tests.api.echo", lambda request, value: value)
    context = routing.resolve("POST", route.path)
    assert api.handle(context, body={"title": "Safe"}).body["data"] == {"title": "Safe"}
    assert api.handle(context, body="bad").status == 400
    secret = register(api, "tests.api.secret", "tests.api.secret", lambda request, value: {"password_hash": "hidden"})
    response = api.handle(routing.resolve("POST", secret.path), body={})
    assert response.status == 400 and "hidden" not in str(response.body)

def test_authentication_then_permission_fail_closed(phase7_kernel: Kernel) -> None:
    users = phase7_kernel.container.resolve("engine.users", UserEngine); auth = phase7_kernel.container.resolve("engine.authentication", AuthenticationEngine)
    permissions = phase7_kernel.container.resolve("engine.permissions", PermissionEngine)
    user = users.create(email="api@example.com", display_name="API", role="member"); auth.set_password(user.user_id, "correct horse battery staple")
    login = auth.login(email="api@example.com", password="correct horse battery staple"); token = login.token.reveal()
    permissions.register(PermissionDefinition("content.read", "tests", "read", "content"))
    api = phase7_kernel.container.resolve("engine.api", APIEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    definition = register(api, "tests.api.protected", "tests.api.protected", lambda request, value: {"user_id": request.authentication.user_id}, protected=True)
    route = routing.resolve("POST", definition.path)
    assert api.handle(route, body={}, credential="forged").status == 401
    assert api.handle(route, body={}, credential=token).status == 403
    permissions.grant_role(RoleGrant("member", "content.read", "tests"))
    response = api.handle(route, body={}, credential=token)
    assert response.status == 200 and response.body["data"]["user_id"] == user.user_id

def test_unexpected_errors_are_safe(phase7_kernel: Kernel) -> None:
    api = phase7_kernel.container.resolve("engine.api", APIEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    definition = register(api, "tests.api.failure", "tests.api.failure", lambda request, value: (_ for _ in ()).throw(RuntimeError("C:\\private\\secret-token")))
    response = api.handle(routing.resolve("POST", definition.path), body={})
    assert response.status == 500
    assert "private" not in str(response.body).lower() and "secret-token" not in str(response.body).lower()

def test_api_has_no_route_registry(phase7_kernel: Kernel) -> None:
    api = phase7_kernel.container.resolve("engine.api", APIEngine)
    assert not hasattr(api, "_routes")
