import pytest
from backend.engines.routing import InvalidRoute, MethodNotAllowed, RouteConflict, RouteDefinition, RouteNotFound, RouteType, RoutingEngine

def route(identifier: str, path: str, methods: tuple[str, ...] = ("GET",)) -> RouteDefinition:
    return RouteDefinition(identifier, "engine.content", RouteType.API, path, methods, "content.operation")

def test_registration_resolution_parameters_and_discovery() -> None:
    engine = RoutingEngine(); engine.register(route("content.api.item", "/content/{identifier}"))
    context = engine.resolve("get", "/content/abc-123")
    assert context.route_id == "content.api.item" and dict(context.parameters) == {"identifier": "abc-123"}
    assert engine.discover() == (engine.discover()[0],)
    assert engine.path_for("content.api.item", identifier="abc-123") == "/content/abc-123"

def test_conflicts_and_methods_fail_deterministically() -> None:
    engine = RoutingEngine(); engine.register(route("content.api.dynamic", "/content/{identifier}"))
    with pytest.raises(RouteConflict): engine.register(route("content.api.static", "/content/about"))
    with pytest.raises(MethodNotAllowed): engine.resolve("POST", "/content/one")
    with pytest.raises(RouteNotFound): engine.resolve("GET", "/missing")

def test_invalid_paths_and_owner_controlled_removal() -> None:
    with pytest.raises(InvalidRoute): route("content.api.bad", "/content/{bad-name}")
    with pytest.raises(InvalidRoute): route("content.api.bad", "/../private")
    engine = RoutingEngine(); engine.register(route("content.api.remove", "/remove"))
    with pytest.raises(InvalidRoute): engine.unregister("content.api.remove", owner="plugin.other")
    engine.unregister("content.api.remove", owner="engine.content")
    with pytest.raises(RouteNotFound): engine.resolve("GET", "/remove")

def test_method_specific_routes_do_not_overlap() -> None:
    engine = RoutingEngine()
    engine.register(route("content.api.read", "/content", ("GET",)))
    engine.register(route("content.api.write", "/content", ("POST",)))
    assert engine.resolve("GET", "/content").route_id == "content.api.read"
    assert engine.resolve("POST", "/content").route_id == "content.api.write"
