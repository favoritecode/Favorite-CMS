"""Fixed, data-only runtimes for bundled first-party Plugin packages."""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urlsplit
from uuid import uuid4

from backend.admin import AdminModule, PluginAdmin
from backend.core.extensions import ManifestValidationError
from backend.engines.api import APIOperation, APIRequest, APIValidationError, PluginAPI
from backend.engines.content import ContentEngine, ContentQuery, ContentSeoMetadata, ContentState
from backend.engines.notifications import (DeliveryStatus, NotificationContract, NotificationEngine,
                                           NotificationRecipient)
from backend.engines.permissions import AuthorizationContext
from backend.engines.rendering import (PluginRendering, PresentationDecorator, PresentationOperation,
    RenderResource, ResourceKind, ResourceOrigin)
from backend.engines.routing import PluginRouting, RouteDefinition, RouteType
from backend.engines.settings import SettingDefinition, SettingScope, SettingScopeKind, SettingsEngine
from backend.engines.plugins.engine import PluginContext

_SPECS = {
    "favorite.plugin.seo": ("seo", frozenset({"admin.register", "api.register", "content.read", "content.update", "rendering.register", "settings.access"})),
    "favorite.plugin.contact": ("contact-form", frozenset({"admin.register", "api.register", "notification.send", "rendering.register", "routing.register", "settings.access"})),
    "favorite.plugin.sitemap": ("sitemap", frozenset({"admin.register", "api.register", "content.read", "rendering.register", "routing.register", "settings.access"})),
    "favorite.plugin.analytics": ("analytics", frozenset({"admin.register", "api.register", "rendering.register", "settings.access"})),
}


def load_first_party_runtime(package: Path, extension_id: str):
    if extension_id == "favorite.plugin.example":
        from backend.engines.plugins.reference import load_reference_runtime
        return load_reference_runtime(package, extension_id)
    try: expected_kind, capabilities = _SPECS[extension_id]
    except KeyError as exc: raise ManifestValidationError("Declarative runtime type is not supported") from exc
    path = package / "contributions.json"
    if not path.is_file() or path.is_symlink(): raise ManifestValidationError("Plugin contribution contract is unavailable")
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc: raise ManifestValidationError("Plugin contribution contract is invalid") from exc
    if not isinstance(value, dict) or set(value) != {"schemaVersion", "kind", "title", "activation"}:
        raise ManifestValidationError("Plugin contribution contract is invalid")
    if value["schemaVersion"] != 1 or value["kind"] != expected_kind or value["activation"] not in {"normal", "fail"}:
        raise ManifestValidationError("Plugin contribution contract is incompatible")
    if not isinstance(value["title"], str) or not 1 <= len(value["title"]) <= 80:
        raise ManifestValidationError("Plugin contribution title is invalid")
    return FirstPartySuiteRuntime(extension_id, expected_kind, value["title"], capabilities, value["activation"] == "fail")


class FirstPartySuiteRuntime:
    def __init__(self, plugin_id: str, kind: str, title: str, capabilities: frozenset[str], fail: bool) -> None:
        self.plugin_id = plugin_id; self.kind = kind; self.title = title; self.capabilities = capabilities; self.fail = fail
        self.settings: SettingsEngine | None = None; self.api: PluginAPI | None = None; self.admin: PluginAdmin | None = None
        self.rendering: PluginRendering | None = None; self.routing: PluginRouting | None = None
        self.content: ContentEngine | None = None; self.notifications: NotificationEngine | None = None
        self.setting_keys: list[str] = []; self.api_targets: list[str] = []; self.route_ids: list[str] = []

    def register(self, context: PluginContext) -> None:
        if context.permissions != self.capabilities: raise ManifestValidationError("Plugin capabilities were not granted exactly")
        self.settings = context.service("engine.settings", SettingsEngine)
        if self.kind == "seo": self._register_seo(context)
        elif self.kind == "contact-form": self._register_contact(context)
        elif self.kind == "sitemap": self._register_sitemap(context)
        else: self._register_analytics(context)

    def activate(self) -> None:
        if self.fail: raise RuntimeError("First-party Plugin activation failed")
    def deactivate(self) -> None: pass
    def unregister(self) -> None:
        if self.routing:
            for route_id in self.route_ids:
                try: self.routing.unregister(route_id)
                except Exception: pass
        if self.api:
            for target in self.api_targets:
                try: self.api.unregister(target)
                except Exception: pass
        if self.rendering: self.rendering.unregister_all()
        if self.admin: self.admin.unregister_all()
        if self.settings:
            for key in self.setting_keys:
                try: self.settings.unregister(key, SettingScopeKind.PLUGIN, self.plugin_id)
                except Exception: pass
        if self.notifications and self.kind == "contact-form":
            try: self.notifications.unregister_contract("favorite.contact.submission", producer=self.plugin_id)
            except Exception: pass

    def _setting(self, key: str, default: object, value_type, validator=None) -> None:
        assert self.settings is not None
        self.settings.register(SettingDefinition(key, self.plugin_id, SettingScopeKind.PLUGIN, value_type,
                                                 default=default, validator=validator))
        self.setting_keys.append(key)
    def _scope(self) -> SettingScope: return SettingScope(SettingScopeKind.PLUGIN, self.plugin_id)
    def _state(self, key: str) -> object:
        assert self.settings is not None
        return self.settings.get(key, self._scope()).value
    def _set(self, key: str, value: object) -> object:
        assert self.settings is not None
        return self.settings.set(key, self._scope(), value).value
    def _phase(self, context: PluginContext, *, route: bool = False) -> None:
        self.rendering = context.service("engine.rendering", PluginRendering)
        if route: self.routing = context.service("engine.routing", PluginRouting)
    def _admin_api(self, context: PluginContext, slug: str, handler, validator=None) -> None:
        self.api = context.service("engine.api", PluginAPI); self.admin = context.service("application.admin", PluginAdmin)
        target = f"{self.plugin_id}.settings"; path = f"/api/plugins/{slug}/settings"
        route = RouteDefinition(f"{self.plugin_id}.api.settings", self.plugin_id, RouteType.API, path, ("GET", "PATCH"), target,
            authentication_required=True, permission="admin.extensions.manage")
        self.api.register(route, APIOperation(target, self.plugin_id, validator or _body_or_empty, handler, lambda value: value,
            authorization=lambda request: AuthorizationContext("manage", "admin_extensions", request.authentication)))
        self.api_targets.append(target)
        self.admin.register_module(AdminModule(f"{self.plugin_id}.admin", self.plugin_id, self.title,
            "/admin/plugins", "admin.extensions.manage", "manage", "admin_extensions", 60))

    def _register_seo(self, context: PluginContext) -> None:
        self._setting("config", {"site_title": "Favorite CMS", "description": "", "canonical_base": "", "robots": "index,follow"}, dict, _seo_config)
        self._admin_api(context, "seo", self._seo_api); self._phase(context)
        self.content = context.service("engine.content", ContentEngine)
        assert self.api
        target = f"{self.plugin_id}.content"; route = RouteDefinition(
            f"{self.plugin_id}.api.content", self.plugin_id, RouteType.API,
            "/api/plugins/seo/content", ("GET", "PATCH"), target,
            authentication_required=True, permission="admin.extensions.manage")
        self.api.register(route, APIOperation(target, self.plugin_id, _seo_content_input,
            self._seo_content_api, lambda value: value,
            authorization=lambda request: AuthorizationContext("manage", "admin_extensions", request.authentication)))
        self.api_targets.append(target)
        assert self.rendering
        self.rendering.register_decorator(PresentationDecorator(f"{self.plugin_id}.head", self.plugin_id, self._seo_decorate, 50))
    def _seo_api(self, request: APIRequest, data: object) -> object:
        if request.route.method == "PATCH":
            if not isinstance(data, dict): raise APIValidationError("SEO configuration is required")
            _seo_config(data); self._set("config", data)
        return self._state("config")
    def _seo_decorate(self, body: str, route, model: object) -> str:
        config = self._state("config"); assert isinstance(config, dict)
        title = str(config["site_title"]); description = str(config["description"]); base = str(config["canonical_base"])
        canonical = base.rstrip("/") + route.matched_path if base else ""
        robots = str(config["robots"]); og_title = title; og_description = description; og_image = ""
        if self.content and base and route.target == "platform.public.content":
            try:
                projection = self.content.seo_projection(route.parameters["content_id"], public_origin=base)
            except Exception:
                projection = None
            if projection:
                title, description, canonical, robots = projection.title, projection.description, projection.canonical, projection.robots
                og_title, og_description, og_image = projection.open_graph_title, projection.open_graph_description, projection.open_graph_image
        tags = [f'<meta name="robots" content="{escape(robots, quote=True)}">',
                f'<meta property="og:site_name" content="{escape(str(config["site_title"]), quote=True)}">',
                f'<meta property="og:title" content="{escape(og_title, quote=True)}">', '<meta property="og:type" content="website">']
        if description: tags += [f'<meta name="description" content="{escape(description, quote=True)}">']
        if canonical: tags += [f'<link rel="canonical" href="{escape(canonical, quote=True)}">', f'<meta property="og:url" content="{escape(canonical, quote=True)}">']
        if og_description: tags += [f'<meta property="og:description" content="{escape(og_description, quote=True)}">']
        if og_image: tags += [f'<meta property="og:image" content="{escape(og_image, quote=True)}">']
        return body.replace("</head>", "".join(tags) + "</head>", 1) if "</head>" in body else body

    def _seo_content_api(self, request: APIRequest, data: object) -> object:
        assert self.content is not None and isinstance(data, dict)
        content_id = str(data["content_id"])
        if request.route.method == "PATCH":
            values = data["metadata"]
            if not isinstance(values, dict): raise APIValidationError("Content SEO metadata is required")
            metadata = ContentSeoMetadata(**values)
            self.content.set_seo_metadata(content_id, metadata, request.authentication)  # type: ignore[arg-type]
        result = self.content.get_seo_metadata(content_id, request.authentication)  # type: ignore[arg-type]
        return {"content_id": content_id, "metadata": result.__dict__}

    def _register_contact(self, context: PluginContext) -> None:
        self._setting("config", {"recipient": "", "delivery": "pending"}, dict, _contact_config)
        self._setting("submissions", [], list, _submissions)
        self._admin_api(context, "contact", self._contact_settings); self._phase(context, route=True)
        self.notifications = context.service("engine.notifications", NotificationEngine)
        self.notifications.register_contract(NotificationContract(
            "favorite.contact.submission", self.plugin_id, _contact_notification_payload,
            _contact_notification_recipient, frozenset({"email"})))
        assert self.api and self.rendering and self.routing and self.admin
        public = RouteDefinition(f"{self.plugin_id}.api.submit", self.plugin_id, RouteType.API, "/api/plugins/contact/submissions", ("POST",), f"{self.plugin_id}.submit")
        self.api.register(public, APIOperation(public.target, self.plugin_id, _contact_input, self._contact_submit, lambda value: value, success_status=201)); self.api_targets.append(public.target)
        manage = RouteDefinition(f"{self.plugin_id}.api.submissions", self.plugin_id, RouteType.API, "/api/plugins/contact/submissions/manage", ("GET",), f"{self.plugin_id}.submissions",
            authentication_required=True, permission="admin.extensions.manage")
        self.api.register(manage, APIOperation(manage.target, self.plugin_id, _empty, lambda r, d: self._state("submissions"), lambda value: value,
            authorization=lambda request: AuthorizationContext("manage", "admin_extensions", request.authentication))); self.api_targets.append(manage.target)
        self.rendering.register_resource(RenderResource(f"{self.plugin_id}.page", ResourceKind.TEMPLATE, ResourceOrigin.PLUGIN, self.plugin_id, self._contact_page))
        self.rendering.register_operation(PresentationOperation(f"{self.plugin_id}.public", self.plugin_id, lambda route: {"title": self.title}, f"{self.plugin_id}.page"))
        route = RouteDefinition(f"{self.plugin_id}.public", self.plugin_id, RouteType.PRESENTATION, "/contact", ("GET",), f"{self.plugin_id}.public")
        self.routing.register(route); self.route_ids.append(route.route_id)
    def _contact_settings(self, request: APIRequest, data: object) -> object:
        if request.route.method == "PATCH":
            if not isinstance(data, dict): raise APIValidationError("Contact configuration is required")
            _contact_config(data); self._set("config", data)
        config = self._state("config"); assert isinstance(config, dict)
        assert self.notifications is not None
        summary = self.notifications.delivery_summary("favorite.contact.submission", producer=self.plugin_id)
        return {**config, "status": {"pending": summary.pending, "delivered": summary.delivered,
                                     "failed": summary.failed, "attempts": summary.attempts,
                                     "provider_available": summary.provider_available}}
    def _contact_submit(self, request: APIRequest, data: object) -> object:
        assert isinstance(data, dict)
        submissions = list(self._state("submissions")); reference = str(uuid4())
        config = self._state("config"); assert isinstance(config, dict)
        delivery_status = "pending"; notification_id = ""
        recipient = str(config["recipient"])
        if recipient:
            assert self.notifications is not None
            result = self.notifications.create("favorite.contact.submission", self.plugin_id,
                NotificationRecipient(recipient, "contact-recipient", recipient), "email",
                {"subject": "New contact submission", "body": f'From: {data["name"]} <{data["email"]}>\n\n{data["message"]}'})
            notification_id = result.notification_id
            if self.notifications.adapter_available("email"):
                result = self.notifications.deliver(notification_id)
            delivery_status = result.status.value
        submissions.append({"reference": reference, "name": data["name"], "email": data["email"], "message": data["message"],
                            "status": delivery_status, "notification_id": notification_id,
                            "created_at": datetime.now(timezone.utc).isoformat()})
        self._set("submissions", submissions[-100:])
        return {"reference": reference, "status": delivery_status}
    def _contact_page(self, values: Mapping[str, object]) -> str:
        return _page(self.title, '<p>Send a message through this site. Submissions remain pending until a delivery provider is configured.</p><form id="contact-form"><label>Name<input name="name" required maxlength="100"></label><label>Email<input name="email" type="email" required maxlength="254"></label><label>Message<textarea name="message" required maxlength="2000"></textarea></label><label class="trap">Website<input name="website" tabindex="-1" autocomplete="off"></label><button type="submit">Send message</button><p role="status" id="contact-status"></p></form><script>document.getElementById("contact-form").addEventListener("submit",async function(e){e.preventDefault();const f=new FormData(e.currentTarget),p=Object.fromEntries(f.entries()),s=document.getElementById("contact-status");try{const r=await fetch("/api/plugins/contact/submissions",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(p)}),v=await r.json();s.textContent=r.ok?"Your message is pending delivery.":(v.error&&v.error.message)||"The message could not be submitted."}catch(_){s.textContent="The message could not be submitted."}});</script>')

    def _register_sitemap(self, context: PluginContext) -> None:
        self._setting("config", {"base_url": "https://example.invalid"}, dict, _sitemap_config)
        self._admin_api(context, "sitemap", self._sitemap_api)
        self._phase(context, route=True); assert self.rendering and self.routing
        content = context.service("engine.content", ContentEngine)
        self.rendering.register_resource(RenderResource(f"{self.plugin_id}.xml", ResourceKind.TEMPLATE, ResourceOrigin.PLUGIN, self.plugin_id, _sitemap_template))
        self.rendering.register_operation(PresentationOperation(f"{self.plugin_id}.public", self.plugin_id,
            lambda route: self._sitemap_model(content), f"{self.plugin_id}.xml", content_type="application/xml; charset=utf-8"))
        route = RouteDefinition(f"{self.plugin_id}.public", self.plugin_id, RouteType.PRESENTATION, "/sitemap.xml", ("GET",), f"{self.plugin_id}.public")
        self.routing.register(route); self.route_ids.append(route.route_id)
    def _sitemap_api(self, request: APIRequest, data: object) -> object:
        if request.route.method == "PATCH":
            if not isinstance(data, dict): raise APIValidationError("Sitemap configuration is required")
            _sitemap_config(data); self._set("config", data)
        return self._state("config")
    def _sitemap_model(self, content: ContentEngine) -> object:
        config = self._state("config"); assert isinstance(config, dict); base = str(config["base_url"]).rstrip("/")
        try: items = content.query(ContentQuery(state=ContentState.PUBLISHED, page_size=100))
        except Exception: items = ()
        return tuple(f"{base}/site/content/{item.content_id}" for item in items)

    def _register_analytics(self, context: PluginContext) -> None:
        self._setting("config", {"provider": "none", "site_id": ""}, dict, _analytics_config)
        self._admin_api(context, "analytics", self._analytics_api); self._phase(context); assert self.rendering
        self.rendering.register_decorator(PresentationDecorator(f"{self.plugin_id}.head", self.plugin_id, self._analytics_decorate, 10))
    def _analytics_api(self, request: APIRequest, data: object) -> object:
        if request.route.method == "PATCH":
            if not isinstance(data, dict): raise APIValidationError("Analytics configuration is required")
            _analytics_config(data); self._set("config", data)
        return self._state("config")
    def _analytics_decorate(self, body: str, route, model: object) -> str:
        config = self._state("config"); assert isinstance(config, dict)
        if config["provider"] == "none": return body
        tag = f'<meta name="favorite-analytics" content="first-party" data-site-id="{escape(str(config["site_id"]), quote=True)}">'
        return body.replace("</head>", tag + "</head>", 1) if "</head>" in body else body


def _body_or_empty(query: Mapping[str, str], body: object) -> object:
    if query: raise APIValidationError("Plugin query is unsupported")
    if body is not None and not isinstance(body, dict): raise APIValidationError("Plugin request is invalid")
    return body
def _seo_content_input(query: Mapping[str, str], body: object) -> object:
    fields = {"description", "canonical_path", "robots", "open_graph_title",
              "open_graph_description", "open_graph_image"}
    if body is None:
        if set(query) != {"content_id"} or not query["content_id"].strip():
            raise APIValidationError("Content SEO query is invalid")
        return {"content_id": query["content_id"]}
    if query or not isinstance(body, dict) or set(body) != {"content_id", "metadata"}:
        raise APIValidationError("Content SEO request is invalid")
    metadata = body["metadata"]
    if not isinstance(metadata, dict) or set(metadata) != fields or any(not isinstance(metadata[key], str) for key in fields):
        raise APIValidationError("Content SEO metadata is invalid")
    return body
def _empty(query: Mapping[str, str], body: object) -> object:
    if query or body is not None: raise APIValidationError("Plugin request contains unsupported input")
    return None
def _seo_config(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"site_title", "description", "canonical_base", "robots"}: raise APIValidationError("SEO configuration is invalid")
    if not isinstance(value["site_title"], str) or not 1 <= len(value["site_title"]) <= 120 or not isinstance(value["description"], str) or len(value["description"]) > 320: raise APIValidationError("SEO configuration is invalid")
    if value["robots"] not in {"index,follow", "noindex,nofollow"}: raise APIValidationError("SEO robots configuration is invalid")
    base = value["canonical_base"]
    if not isinstance(base, str): raise APIValidationError("SEO canonical configuration is invalid")
    if base:
        parsed = urlsplit(base)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment: raise APIValidationError("SEO canonical configuration is invalid")
def _contact_config(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"recipient", "delivery"} or value.get("delivery") != "pending" or not isinstance(value.get("recipient"), str) or len(value["recipient"]) > 254: raise APIValidationError("Contact configuration is invalid")
    if value["recipient"] and not re.fullmatch(r"[^@\s]{1,64}@[^@\s]{1,189}", value["recipient"]): raise APIValidationError("Contact recipient is invalid")
def _contact_input(query: Mapping[str, str], body: object) -> object:
    if query or not isinstance(body, dict) or set(body) != {"name", "email", "message", "website"}: raise APIValidationError("Contact submission is invalid")
    if body["website"] != "" or not isinstance(body["name"], str) or not 1 <= len(body["name"].strip()) <= 100 or not isinstance(body["email"], str) or not re.fullmatch(r"[^@\s]{1,64}@[^@\s]{1,189}", body["email"]) or not isinstance(body["message"], str) or not 1 <= len(body["message"].strip()) <= 2000: raise APIValidationError("Contact submission is invalid")
    return {key: str(body[key]).strip() for key in ("name", "email", "message")}
def _submissions(value: object) -> None:
    if not isinstance(value, list) or len(value) > 100 or any(not isinstance(item, dict) for item in value): raise APIValidationError("Contact submissions are invalid")
def _contact_notification_payload(value: Mapping[str, object]) -> None:
    if set(value) != {"subject", "body"} or not isinstance(value["subject"], str) or not isinstance(value["body"], str):
        raise APIValidationError("Contact Notification is invalid")
    if not 1 <= len(value["subject"].strip()) <= 200 or not 1 <= len(value["body"].strip()) <= 3000:
        raise APIValidationError("Contact Notification is invalid")
def _contact_notification_recipient(value: NotificationRecipient) -> None:
    if value.scope != "contact-recipient" or not re.fullmatch(r"[^@\s]{1,64}@[^@\s]{1,189}", value.destination):
        raise APIValidationError("Contact Notification recipient is invalid")
def _sitemap_config(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"base_url"} or not isinstance(value["base_url"], str): raise APIValidationError("Sitemap configuration is invalid")
    parsed = urlsplit(value["base_url"])
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment: raise APIValidationError("Sitemap configuration is invalid")
def _analytics_config(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"provider", "site_id"} or value["provider"] not in {"none", "first-party"} or not isinstance(value["site_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{0,64}", value["site_id"]): raise APIValidationError("Analytics configuration is invalid")
    if value["provider"] == "first-party" and not value["site_id"]: raise APIValidationError("Analytics site identity is required")
def _sitemap_template(values: Mapping[str, object]) -> str:
    model = values.get("model"); items = model if isinstance(model, tuple) else ()
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{escape(str(url))}</loc></url>" for url in items) + "</urlset>"
def _page(title: str, content: str) -> str:
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="favorite-renderer" content="backend"><title>{escape(title)}</title><style>body{{font-family:system-ui;background:#f8fafc;color:#0f172a;margin:0}}main{{max-width:42rem;margin:8vh auto;padding:2rem}}form{{display:grid;gap:1rem;background:white;padding:2rem;border:1px solid #cbd5e1;border-radius:1rem}}label{{display:grid;gap:.35rem}}input,textarea,button{{font:inherit;padding:.7rem}}textarea{{min-height:8rem}}button{{background:#075985;color:white;border:0;border-radius:.5rem}}.trap{{position:absolute;left:-10000px}}</style></head><body><main><h1>{escape(title)}</h1>{content}<p><a href="/site/welcome">Return to the site</a></p></main></body></html>'
