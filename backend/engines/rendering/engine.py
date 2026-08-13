"""Presentation composition over an already-resolved Route Context."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import html
import re
from types import MappingProxyType
from typing import Callable, Mapping
from uuid import uuid4

from backend.core.container import ServiceContainer
from backend.engines.errors import ApplicationFailure, ErrorHandlingEngine, ValidationFailure
from backend.engines.authentication import AuthenticationContext, AuthenticationEngine
from backend.engines.permissions import AuthorizationContext, PermissionDenied, PermissionEngine
from backend.engines.routing import RouteContext, RouteType
from backend.engines.themes import ThemeEngine
from backend.engines.plugins import PluginEngine

class RenderingFailure(ApplicationFailure): pass
class InvalidRenderResource(ValidationFailure): pass
class RenderResourceNotFound(RenderingFailure): pass
class RenderingAuthenticationRequired(RenderingFailure): pass

class ResourceOrigin(StrEnum):
    PLATFORM = "platform"
    PLUGIN = "plugin"
    THEME = "theme"
class ResourceKind(StrEnum):
    TEMPLATE = "template"; LAYOUT = "layout"; COMPONENT = "component"; WIDGET = "widget"

Renderer = Callable[[Mapping[str, object]], str]
Decorator = Callable[[str, RouteContext, object], str]
ResourceResolver = Callable[[RouteContext], object]
PresentationAuthorization = Callable[[RouteContext, AuthenticationContext], AuthorizationContext]

@dataclass(frozen=True)
class RenderResource:
    resource_id: str
    kind: ResourceKind
    origin: ResourceOrigin
    owner: str
    renderer: Renderer
    priority: int = 0
    theme_id: str | None = None
    package_reference: str | None = None
    optional: bool = False
    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{2,127}", self.resource_id) or not self.owner.strip():
            raise InvalidRenderResource("Render resource identity is invalid")
        if self.origin is ResourceOrigin.THEME and not self.theme_id:
            raise InvalidRenderResource("Theme resource requires Theme identity")
        if self.origin is ResourceOrigin.THEME and not self.package_reference:
            raise InvalidRenderResource("Theme resource requires a package reference")
        if self.origin is not ResourceOrigin.THEME and self.theme_id is not None:
            raise InvalidRenderResource("Non-Theme resource cannot declare Theme identity")
        if self.origin is not ResourceOrigin.THEME and self.package_reference is not None:
            raise InvalidRenderResource("Non-Theme resource cannot declare a Theme package reference")

@dataclass(frozen=True)
class PresentationOperation:
    target: str
    owner: str
    resolver: ResourceResolver
    template: str
    layout: str | None = None
    components: tuple[str, ...] = ()
    widgets: tuple[str, ...] = ()
    authorization: PresentationAuthorization | None = None
    content_type: str = "text/html; charset=utf-8"
    def __post_init__(self) -> None:
        if not self.target.strip() or not self.owner.strip() or not self.template.strip():
            raise InvalidRenderResource("Presentation operation is invalid")
        if self.content_type not in {"text/html; charset=utf-8", "application/xml; charset=utf-8"}:
            raise InvalidRenderResource("Presentation content type is invalid")

@dataclass(frozen=True)
class PresentationDecorator:
    decorator_id: str
    owner: str
    apply: Decorator
    priority: int = 0
    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{2,127}", self.decorator_id) or not self.owner.strip() or not callable(self.apply):
            raise InvalidRenderResource("Presentation decorator is invalid")

@dataclass(frozen=True)
class RenderContext:
    request_id: str
    route: RouteContext
    active_theme: str
    model: object
    template: str
    layout: str | None
    components: Mapping[str, str]
    widgets: Mapping[str, str]
    assets: tuple[str, ...]

@dataclass(frozen=True)
class RenderResponse:
    status: int
    body: str
    content_type: str = "text/html; charset=utf-8"
    headers: Mapping[str, str] = MappingProxyType({})

class RenderingEngine:
    engine_id = "rendering"
    dependencies = ("routing", "themes", "content", "media", "localization", "menu", "seo", "permissions", "cache")
    def __init__(self) -> None:
        self._themes: ThemeEngine | None = None; self._errors: ErrorHandlingEngine | None = None
        self._authentication: AuthenticationEngine | None = None; self._permissions: PermissionEngine | None = None
        self._resources: dict[str, list[RenderResource]] = {}; self._operations: dict[str, PresentationOperation] = {}
        self._decorators: dict[str, PresentationDecorator] = {}
        self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._themes = container.resolve("engine.themes", ThemeEngine)
        self._errors = container.resolve("core.errors", ErrorHandlingEngine)
        self._authentication = container.resolve("engine.authentication", AuthenticationEngine)
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        container.register("engine.rendering", self)
        container.resolve("engine.plugins", PluginEngine).publish_phase_service("engine.rendering", self)
    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False; self._resources.clear(); self._operations.clear(); self._decorators.clear()
    def register_resource(self, resource: RenderResource) -> None:
        if resource.origin is ResourceOrigin.THEME:
            package = self._themes_required().package(resource.theme_id or "")
            declared = {ResourceKind.TEMPLATE: package.templates, ResourceKind.LAYOUT: package.layouts,
                        ResourceKind.COMPONENT: package.components, ResourceKind.WIDGET: package.widgets}[resource.kind]
            if resource.package_reference not in declared:
                raise InvalidRenderResource("Theme rendering resource is not declared by its package")
        choices = self._resources.setdefault(resource.resource_id, [])
        if any(item.origin is resource.origin and item.owner == resource.owner and item.theme_id == resource.theme_id for item in choices):
            raise InvalidRenderResource("Render resource registration conflicts")
        choices.append(resource)
        choices.sort(key=lambda item: (-_origin_rank(item.origin), -item.priority, item.owner))
    def unregister_owner(self, owner: str) -> None:
        for identifier in tuple(self._resources):
            remaining = [item for item in self._resources[identifier] if item.owner != owner]
            if remaining: self._resources[identifier] = remaining
            else: del self._resources[identifier]
        for target in tuple(self._operations):
            if self._operations[target].owner == owner: del self._operations[target]
        for identifier in tuple(self._decorators):
            if self._decorators[identifier].owner == owner: del self._decorators[identifier]
    def for_plugin(self, plugin_id: str) -> "PluginRendering": return PluginRendering(self, plugin_id)
    def register_operation(self, operation: PresentationOperation) -> None:
        if operation.target in self._operations: raise InvalidRenderResource("Presentation operation is already registered")
        self._operations[operation.target] = operation
    def register_decorator(self, decorator: PresentationDecorator) -> None:
        if decorator.decorator_id in self._decorators: raise InvalidRenderResource("Presentation decorator is already registered")
        self._decorators[decorator.decorator_id] = decorator
    def render(self, route: RouteContext, *, request_id: str | None = None,
               credential: str | None = None) -> RenderResponse:
        request_id = request_id or str(uuid4())
        try:
            if route.route_type is not RouteType.PRESENTATION: raise InvalidRenderResource("Route is not a presentation Route")
            operation = self._operations.get(route.target)
            if operation is None or operation.owner != route.owner: raise RenderResourceNotFound("Presentation operation is unavailable")
            authentication = self._authentication_required().resolve(credential)
            if route.authentication_required and not authentication.authenticated:
                raise RenderingAuthenticationRequired("Authentication is required")
            if route.permission is not None:
                if operation.authorization is None: raise RenderingFailure("Authorization contract is unavailable")
                self._permissions_required().require(route.permission, operation.authorization(route, authentication))
            active_theme = self._themes_required().active_theme
            if active_theme is None: raise RenderResourceNotFound("An active Theme is required")
            package = self._themes_required().package(active_theme)
            model = operation.resolver(route)
            component_output = self._render_optional(operation.components, ResourceKind.COMPONENT, active_theme, model)
            widget_output = self._render_optional(operation.widgets, ResourceKind.WIDGET, active_theme, model)
            template = self._select(operation.template, ResourceKind.TEMPLATE, active_theme)
            values: Mapping[str, object] = MappingProxyType({"model": model, "components": component_output, "widgets": widget_output})
            body = template.renderer(values)
            layout_id: str | None = None
            if operation.layout is not None:
                layout = self._select(operation.layout, ResourceKind.LAYOUT, active_theme)
                layout_id = layout.resource_id
                body = layout.renderer(MappingProxyType({"body": body, "model": model}))
            if not isinstance(body, str): raise RenderingFailure("Rendering produced an invalid response")
            if operation.content_type.startswith("text/html"):
                for decorator in sorted(self._decorators.values(), key=lambda item: (-item.priority, item.decorator_id)):
                    try:
                        decorated = decorator.apply(body, route, model)
                        if not isinstance(decorated, str): raise RenderingFailure("Presentation decorator returned invalid output")
                        body = decorated
                    except Exception:
                        # Optional Plugin presentation contributions cannot make the owning page unavailable.
                        continue
            assets = tuple(dict.fromkeys(package.assets))
            context = RenderContext(request_id, route, active_theme, model, template.resource_id, layout_id,
                                    MappingProxyType(component_output), MappingProxyType(widget_output), assets)
            return RenderResponse(200, body, content_type=operation.content_type, headers=MappingProxyType({"x-request-id": context.request_id}))
        except Exception as exc:
            record = self._errors_required().normalize(exc, source="engine.rendering", context={"request_id": request_id, "route_id": route.route_id})
            status = (401 if isinstance(exc, RenderingAuthenticationRequired) else
                      403 if isinstance(exc, PermissionDenied) else
                      404 if isinstance(exc, RenderResourceNotFound) else
                      400 if isinstance(exc, InvalidRenderResource) else 500)
            return RenderResponse(status, "<!doctype html><title>Request failed</title><h1>" + html.escape(record.safe_message) + "</h1>", headers=MappingProxyType({"x-error-id": record.error_id, "x-request-id": request_id}))
    def _render_optional(self, identifiers: tuple[str, ...], kind: ResourceKind, theme: str, model: object) -> dict[str, str]:
        result: dict[str, str] = {}
        for identifier in identifiers:
            try:
                resource = self._select(identifier, kind, theme)
                value = resource.renderer(MappingProxyType({"model": model}))
                if not isinstance(value, str): raise RenderingFailure("Renderable resource returned invalid output")
                result[identifier] = value
            except Exception:
                choices = self._resources.get(identifier, [])
                if not any(item.optional for item in choices): raise
        return result
    def _select(self, identifier: str, kind: ResourceKind, active_theme: str) -> RenderResource:
        eligible = [item for item in self._resources.get(identifier, ()) if item.kind is kind and (item.origin is not ResourceOrigin.THEME or item.theme_id == active_theme)]
        if not eligible: raise RenderResourceNotFound("Required rendering resource is unavailable")
        return eligible[0]
    def _themes_required(self) -> ThemeEngine:
        if self._themes is None: raise RuntimeError("Rendering Engine is not initialized")
        return self._themes
    def _errors_required(self) -> ErrorHandlingEngine:
        if self._errors is None: raise RuntimeError("Rendering Engine is not initialized")
        return self._errors
    def _authentication_required(self) -> AuthenticationEngine:
        if self._authentication is None: raise RuntimeError("Rendering Engine is not initialized")
        return self._authentication
    def _permissions_required(self) -> PermissionEngine:
        if self._permissions is None: raise RuntimeError("Rendering Engine is not initialized")
        return self._permissions

def _origin_rank(origin: ResourceOrigin) -> int:
    return {ResourceOrigin.THEME: 3, ResourceOrigin.PLUGIN: 2, ResourceOrigin.PLATFORM: 1}[origin]

class PluginRendering:
    def __init__(self, rendering: RenderingEngine, plugin_id: str) -> None: self._rendering = rendering; self._plugin_id = plugin_id
    def register_resource(self, resource: RenderResource) -> None:
        if resource.origin is not ResourceOrigin.PLUGIN or resource.owner != self._plugin_id:
            raise InvalidRenderResource("Plugin rendering resource owner is invalid")
        self._rendering.register_resource(resource)
    def register_operation(self, operation: PresentationOperation) -> None:
        if operation.owner != self._plugin_id: raise InvalidRenderResource("Plugin presentation owner is invalid")
        self._rendering.register_operation(operation)
    def register_decorator(self, decorator: PresentationDecorator) -> None:
        if decorator.owner != self._plugin_id: raise InvalidRenderResource("Plugin presentation decorator owner is invalid")
        self._rendering.register_decorator(decorator)
    def unregister_all(self) -> None: self._rendering.unregister_owner(self._plugin_id)
