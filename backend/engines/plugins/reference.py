"""Strict data-only runtime for the bundled first-party reference Plugin."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from backend.admin import AdminModule, PluginAdmin
from backend.core.extensions import ManifestValidationError
from backend.engines.api import APIOperation, APIRequest, APIValidationError, PluginAPI
from backend.engines.permissions import AuthorizationContext
from backend.engines.rendering import (PluginRendering, PresentationOperation, RenderResource,
    ResourceKind, ResourceOrigin)
from backend.engines.routing import PluginRouting, RouteDefinition, RouteType
from backend.engines.settings import SettingDefinition, SettingScope, SettingScopeKind, SettingsEngine
from backend.engines.plugins.engine import PluginContext

_CAPABILITIES = frozenset({"admin.register", "api.register", "rendering.register",
                           "routing.register", "settings.access"})
_ID = "favorite.plugin.example"


def load_reference_runtime(package: Path, extension_id: str) -> "ReferencePluginRuntime":
    if extension_id != _ID:
        raise ManifestValidationError("Declarative runtime type is not supported")
    path = package / "contributions.json"
    if not path.is_file() or path.is_symlink():
        raise ManifestValidationError("Plugin contribution contract is unavailable")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestValidationError("Plugin contribution contract is invalid") from exc
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "kind", "title", "defaultMessage", "activation"}:
        raise ManifestValidationError("Plugin contribution contract is invalid")
    if value["schemaVersion"] != 1 or value["kind"] != "reference-message":
        raise ManifestValidationError("Plugin contribution contract is incompatible")
    title, message, activation = value["title"], value["defaultMessage"], value["activation"]
    if not isinstance(title, str) or not 1 <= len(title) <= 80 or not isinstance(message, str) or not 1 <= len(message) <= 280:
        raise ManifestValidationError("Plugin contribution text is invalid")
    if activation not in {"normal", "fail"}:
        raise ManifestValidationError("Plugin activation behavior is invalid")
    return ReferencePluginRuntime(title, message, activation == "fail")


class ReferencePluginRuntime:
    def __init__(self, title: str, message: str, fail_activation: bool = False) -> None:
        self._title = title; self._message = message; self._fail_activation = fail_activation
        self._settings: SettingsEngine | None = None; self._context: PluginContext | None = None
        self._api: PluginAPI | None = None; self._admin: PluginAdmin | None = None
        self._rendering: PluginRendering | None = None; self._routing: PluginRouting | None = None
        self._registered = False

    def register(self, context: PluginContext) -> None:
        if context.permissions != _CAPABILITIES:
            raise ManifestValidationError("Reference Plugin capabilities were not granted exactly")
        self._context = context
        settings = context.service("engine.settings", SettingsEngine)
        settings.register(SettingDefinition("message", _ID, SettingScopeKind.PLUGIN, str,
            default=self._message, validator=_message_value))
        self._settings = settings
        api = context.service("engine.api", PluginAPI)
        self._api = api
        route = RouteDefinition("favorite.plugin.example.api", _ID, RouteType.API,
            "/api/plugins/example", ("GET", "PATCH"), "favorite.plugin.example.state",
            authentication_required=True, permission="admin.extensions.manage")
        api.register(route, APIOperation(route.target, _ID, _input, self._handle, lambda value: value,
            authorization=lambda request: AuthorizationContext("manage", "admin_extensions", request.authentication)))
        admin = context.service("application.admin", PluginAdmin); self._admin = admin
        admin.register_module(AdminModule(
            "favorite.plugin.example.admin", _ID, "Example Plugin", "/admin/manage#plugin-example",
            "admin.extensions.manage", "manage", "admin_extensions", 55))
        rendering = context.service("engine.rendering", PluginRendering)
        self._rendering = rendering
        rendering.register_resource(RenderResource("favorite.plugin.example.page", ResourceKind.TEMPLATE,
            ResourceOrigin.PLUGIN, _ID, self._render))
        rendering.register_operation(PresentationOperation("favorite.plugin.example.public", _ID,
            self._model, "favorite.plugin.example.page"))
        routing = context.service("engine.routing", PluginRouting); self._routing = routing
        routing.register(RouteDefinition(
            "favorite.plugin.example.public", _ID, RouteType.PRESENTATION, "/plugins/example", ("GET",),
            "favorite.plugin.example.public"))
        self._registered = True

    def activate(self) -> None:
        if self._fail_activation:
            raise RuntimeError("Reference Plugin activation failed")

    def deactivate(self) -> None: pass

    def unregister(self) -> None:
        if self._routing is not None:
            try: self._routing.unregister("favorite.plugin.example.public")
            except Exception: pass
        if self._api is not None:
            try: self._api.unregister("favorite.plugin.example.state")
            except Exception: pass
        if self._rendering is not None: self._rendering.unregister_all()
        if self._admin is not None: self._admin.unregister_all()
        if self._registered and self._settings is not None:
            try: self._settings.unregister("message", SettingScopeKind.PLUGIN, _ID)
            except Exception: pass
        self._registered = False

    def _value(self, authentication=None) -> str:
        if self._settings is None: raise APIValidationError("Plugin state is unavailable")
        value = self._settings.get("message", SettingScope(SettingScopeKind.PLUGIN, _ID), authentication).value
        if not isinstance(value, str): raise APIValidationError("Plugin state is invalid")
        return value

    def _handle(self, request: APIRequest, data: object) -> Mapping[str, object]:
        if request.route.method == "PATCH":
            if not isinstance(data, dict): raise APIValidationError("Plugin request is invalid")
            if self._settings is None: raise APIValidationError("Plugin state is unavailable")
            self._settings.set("message", SettingScope(SettingScopeKind.PLUGIN, _ID), data["message"], request.authentication)
        elif data is not None: raise APIValidationError("Plugin request body is unsupported")
        return MappingProxyType({"plugin": _ID, "title": self._title,
                                 "message": self._value(request.authentication), "active": True})

    def _model(self, route) -> Mapping[str, object]:
        return MappingProxyType({"title": self._title, "message": self._value()})

    def _render(self, values: Mapping[str, object]) -> str:
        model = values.get("model"); model = model if isinstance(model, Mapping) else {}
        return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="favorite-renderer" content="backend"><meta name="plugin" content="favorite.plugin.example">'
            f'<title>{escape(str(model.get("title", self._title)))}</title><style>body{{margin:0;font-family:system-ui;background:#f8fafc;color:#0f172a}}main{{max-width:52rem;margin:10vh auto;padding:2rem}}article{{background:white;border:1px solid #e2e8f0;border-radius:1.25rem;padding:clamp(2rem,6vw,4rem);box-shadow:0 20px 50px #0f172a12}}a{{color:#0369a1}}p{{font-size:1.15rem;line-height:1.7}}</style></head>'
            f'<body><main><article><p>First-party Plugin</p><h1>{escape(str(model.get("title", self._title)))}</h1><p>{escape(str(model.get("message", self._message)))}</p><a href="/site/welcome">Return to the site</a></article></main></body></html>')


def _message_value(value: object) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 280 or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value):
        raise APIValidationError("Plugin message is invalid")

def _input(query: Mapping[str, str], body: object) -> object:
    if query: raise APIValidationError("Plugin request query is unsupported")
    if body is None: return None
    if not isinstance(body, dict) or set(body) != {"message"}:
        raise APIValidationError("Plugin request is invalid")
    _message_value(body["message"])
    return body
