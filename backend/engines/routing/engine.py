"""Authoritative route registry, matcher, and Route Context owner."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from types import MappingProxyType
from typing import Mapping

from backend.core.container import ServiceContainer
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.plugins import PluginEngine

class RoutingFailure(ApplicationFailure): pass
class InvalidRoute(ValidationFailure): pass
class RouteConflict(ValidationFailure): pass
class RouteNotFound(RoutingFailure): pass
class MethodNotAllowed(RoutingFailure): pass

class RouteType(StrEnum):
    API = "api"
    PRESENTATION = "presentation"

_ID = re.compile(r"^[a-z][a-z0-9_.-]{2,127}$")
_PARAM = re.compile(r"^\{([a-z][a-z0-9_]*)\}$")
_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})

@dataclass(frozen=True)
class RouteDefinition:
    route_id: str
    owner: str
    route_type: RouteType
    path: str
    methods: tuple[str, ...]
    target: str
    authentication_required: bool = False
    permission: str | None = None
    active: bool = True

    def __post_init__(self) -> None:
        if not _ID.fullmatch(self.route_id) or not _ID.fullmatch(self.owner) or not _ID.fullmatch(self.target):
            raise InvalidRoute("Route identity, owner, or target is invalid")
        segments = _segments(self.path)
        names: list[str] = []
        for segment in segments:
            match = _PARAM.fullmatch(segment)
            if "{" in segment or "}" in segment:
                if match is None: raise InvalidRoute("Route parameter declaration is invalid")
                names.append(match.group(1))
        if len(names) != len(set(names)): raise InvalidRoute("Route parameters must be unique")
        normalized = tuple(dict.fromkeys(method.upper() for method in self.methods))
        if not normalized or any(method not in _METHODS for method in normalized):
            raise InvalidRoute("Route method is invalid")
        object.__setattr__(self, "methods", normalized)
        if self.permission is not None and not self.permission.strip():
            raise InvalidRoute("Route permission is invalid")

@dataclass(frozen=True)
class RouteContext:
    route_id: str
    owner: str
    route_type: RouteType
    matched_path: str
    method: str
    target: str
    parameters: Mapping[str, str]
    authentication_required: bool
    permission: str | None

class RoutingEngine:
    engine_id = "routing"
    dependencies = ("plugins", "themes")
    def __init__(self) -> None:
        self._routes: dict[str, RouteDefinition] = {}; self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        container.register("engine.routing", self)
        container.resolve("engine.plugins", PluginEngine).publish_phase_service("engine.routing", self)
    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False; self._routes.clear()
    def register(self, route: RouteDefinition) -> None:
        if route.route_id in self._routes: raise RouteConflict("Route identifier is already registered")
        for existing in self._routes.values():
            if set(route.methods) & set(existing.methods) and _patterns_overlap(route.path, existing.path):
                raise RouteConflict("Route registration is ambiguous")
        self._routes[route.route_id] = route
    def unregister(self, route_id: str, *, owner: str) -> None:
        route = self._routes.get(route_id)
        if route is None: raise RouteNotFound("Route is not registered")
        if route.owner != owner: raise InvalidRoute("Route owner cannot unregister this Route")
        del self._routes[route_id]
    def unregister_owner(self, owner: str) -> None:
        for identifier in tuple(self._routes):
            if self._routes[identifier].owner == owner: del self._routes[identifier]
    def for_plugin(self, plugin_id: str) -> "PluginRouting": return PluginRouting(self, plugin_id)
    def set_active(self, route_id: str, *, owner: str, active: bool) -> None:
        route = self._routes.get(route_id)
        if route is None: raise RouteNotFound("Route is not registered")
        if route.owner != owner: raise InvalidRoute("Route owner cannot modify this Route")
        self._routes[route_id] = RouteDefinition(**{**route.__dict__, "active": active})
    def discover(self) -> tuple[RouteDefinition, ...]:
        return tuple(self._routes[key] for key in sorted(self._routes))
    def resolve(self, method: str, path: str) -> RouteContext:
        normalized_method = method.upper()
        incoming = _segments(path)
        path_matches: list[tuple[RouteDefinition, dict[str, str]]] = []
        for route in self._routes.values():
            values = _match(route.path, incoming)
            if values is not None and route.active: path_matches.append((route, values))
        if not path_matches: raise RouteNotFound("Route was not found")
        method_matches = [(route, values) for route, values in path_matches if normalized_method in route.methods]
        if not method_matches: raise MethodNotAllowed("Request method is not supported")
        if len(method_matches) != 1: raise RoutingFailure("Route resolution is ambiguous")
        route, values = method_matches[0]
        return RouteContext(route.route_id, route.owner, route.route_type, path, normalized_method,
                            route.target, MappingProxyType(values), route.authentication_required, route.permission)
    def path_for(self, route_id: str, **parameters: str) -> str:
        route = self._routes.get(route_id)
        if route is None or not route.active: raise RouteNotFound("Route is unavailable")
        result = route.path
        expected = {m.group(1) for part in _segments(route.path) if (m := _PARAM.fullmatch(part))}
        if set(parameters) != expected: raise InvalidRoute("Route parameters do not match the contract")
        for name, value in parameters.items():
            if not value or "/" in value or "\\" in value or value in {".", ".."}: raise InvalidRoute("Route parameter is invalid")
            result = result.replace("{" + name + "}", value)
        return result

def _segments(path: str) -> tuple[str, ...]:
    if not isinstance(path, str) or not path.startswith("/") or len(path) > 2048 or "?" in path or "#" in path or "\\" in path or "\x00" in path:
        raise InvalidRoute("Route path is invalid")
    if path != "/" and path.endswith("/"): path = path[:-1]
    parts = tuple(part for part in path.split("/")[1:] if part)
    if "//" in path or any(part in {".", ".."} for part in parts): raise InvalidRoute("Route path is invalid")
    return parts
def _patterns_overlap(left: str, right: str) -> bool:
    a, b = _segments(left), _segments(right)
    return len(a) == len(b) and all(x == y or _PARAM.fullmatch(x) or _PARAM.fullmatch(y) for x, y in zip(a, b))
def _match(pattern: str, incoming: tuple[str, ...]) -> dict[str, str] | None:
    expected = _segments(pattern)
    if len(expected) != len(incoming): return None
    values: dict[str, str] = {}
    for route_part, value in zip(expected, incoming):
        match = _PARAM.fullmatch(route_part)
        if match:
            if not value or value in {".", ".."}: return None
            values[match.group(1)] = value
        elif route_part != value: return None
    return values

class PluginRouting:
    def __init__(self, routing: RoutingEngine, plugin_id: str) -> None: self._routing = routing; self._plugin_id = plugin_id
    def register(self, route: RouteDefinition) -> None:
        if route.owner != self._plugin_id: raise InvalidRoute("Plugin Route owner is invalid")
        self._routing.register(route)
    def unregister(self, route_id: str) -> None: self._routing.unregister(route_id, owner=self._plugin_id)
