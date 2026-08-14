"""Generic CMS management and public experience API coordination."""
from __future__ import annotations

from html import escape
from typing import Mapping
from urllib.parse import quote

from backend.admin.engine import AdminEngine, AdminModule
from backend.admin.article import article_text, normalize_slug, sanitize_article_html, valid_slug
from backend.core.container import ServiceContainer
from backend.core.extensions import ExtensionManager
from backend.engines.api import APIEngine, APIOperation, APIRequest, APIResourceNotFound, APIValidationError
from backend.engines.content import ContentEngine, ContentField, ContentQuery, ContentState, ContentType, FieldKind
from backend.engines.localization import Language, Locale, LocalizationEngine, TranslationResource
from backend.engines.media import MediaAccessContract, MediaEngine, MediaType
from backend.engines.permissions import AuthorizationContext, PermissionDefinition, PermissionEngine
from backend.engines.plugins import PluginEngine
from backend.engines.rendering import PresentationOperation, RenderResource, RenderResourceNotFound, RenderingEngine, ResourceKind, ResourceOrigin
from backend.engines.routing import RouteDefinition, RouteType, RoutingEngine
from backend.engines.search import ResourceVisibility, SearchDocument, SearchEngine, SearchQuery, SearchableType
from backend.engines.settings import SettingDefinition, SettingScope, SettingScopeKind, SettingsEngine
from backend.engines.themes import ThemeEngine
from backend.operations.health import HealthEngine

OWNER = "application.admin.platform"
PERMISSIONS = {"content": "admin.content.manage", "media": "admin.media.manage",
               "settings": "admin.settings.manage", "extensions": "admin.extensions.manage",
               "diagnostics": "admin.diagnostics.view"}
CONTENT_PERMISSIONS = {action: f"platform.content.{action}" for action in ("create", "read", "update", "delete", "publish", "archive")}
MEDIA_PERMISSIONS = {action: f"platform.media.{action}" for action in ("create", "read", "update", "delete")}
SETTING_PERMISSIONS = {"read": "platform.setting.read", "write": "platform.setting.write"}


class AdminPlatformEngine:
    engine_id = "admin_platform"
    dependencies = ("admin", "content", "media", "settings", "search", "localization", "plugins", "themes", "observability", "rendering")
    def __init__(self) -> None: self._container: ServiceContainer | None = None; self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._container = container; container.register("application.admin.platform", self)
    def start(self) -> None:
        permissions = self._service("engine.permissions", PermissionEngine)
        self._register_platform_contracts(permissions)
        for area, permission_id in PERMISSIONS.items():
            action = "view" if area == "diagnostics" else "manage"
            permissions.register(PermissionDefinition(permission_id, OWNER, action, f"admin_{area}"))
        admin = self._service("application.admin", AdminEngine)
        destinations = {"content": "/admin/pages", "media": "/admin/media",
                        "settings": "/admin/settings", "extensions": "/admin/themes",
                        "diagnostics": "/admin/diagnostics"}
        for order, (area, permission_id) in enumerate(PERMISSIONS.items(), 10):
            action = "view" if area == "diagnostics" else "manage"
            admin.register_module(AdminModule(f"admin.{area}", OWNER, area.title(), destinations[area], permission_id, action, f"admin_{area}", order))
        api = self._service("engine.api", APIEngine)
        self._register(api, "content", "/admin/api/content", ("GET", "POST", "PATCH", "DELETE"), self._content, "content")
        self._register(api, "content_preview", "/admin/api/content/preview", ("POST",), self._content_preview, "content")
        self._register(api, "content_capabilities", "/admin/api/content/capabilities", ("GET",), self._content_capabilities, "content")
        self._register(api, "media", "/admin/api/media", ("GET", "POST"), self._media, "media")
        self._register(api, "settings", "/admin/api/settings", ("GET", "PATCH"), self._settings, "settings")
        self._register(api, "extensions", "/admin/api/extensions", ("GET", "POST"), self._extensions, "extensions")
        self._register(api, "diagnostics", "/admin/api/diagnostics", ("GET",), self._diagnostics, "diagnostics")
        api.register(RouteDefinition("admin.platform.dashboard", OWNER, RouteType.API, "/admin/api/dashboard", ("GET",),
                                     "admin.platform.dashboard", authentication_required=True),
                     APIOperation("admin.platform.dashboard", OWNER, _query_only, self._dashboard, lambda value: value))
        api.register(RouteDefinition("platform.search", OWNER, RouteType.API, "/api/search", ("GET",), "platform.search"), APIOperation("platform.search", OWNER, _query_only, self._search, lambda value: value))
        api.register(RouteDefinition("platform.localization", OWNER, RouteType.API, "/api/localization", ("GET",), "platform.localization"), APIOperation("platform.localization", OWNER, _query_only, self._localize, lambda value: value))
        self._service("engine.routing", RoutingEngine).register(RouteDefinition("platform.public.page", OWNER, RouteType.PRESENTATION, "/site/{slug}", ("GET",), "platform.public.page"))
        self._service("engine.routing", RoutingEngine).register(RouteDefinition("platform.public.content", OWNER, RouteType.PRESENTATION, "/site/content/{content_id}", ("GET",), "platform.public.content"))
        self._service("engine.routing", RoutingEngine).register(RouteDefinition("platform.public.search", OWNER, RouteType.PRESENTATION, "/site/search/{query}", ("GET",), "platform.public.search"))
        rendering = self._service("engine.rendering", RenderingEngine)
        rendering.register_resource(RenderResource("platform.page", ResourceKind.TEMPLATE, ResourceOrigin.PLATFORM, OWNER, _page_template))
        rendering.register_resource(RenderResource("starter.header", ResourceKind.COMPONENT, ResourceOrigin.PLATFORM, OWNER, _fallback_header))
        rendering.register_resource(RenderResource("starter.footer", ResourceKind.COMPONENT, ResourceOrigin.PLATFORM, OWNER, _fallback_footer))
        rendering.register_resource(RenderResource("starter.base", ResourceKind.LAYOUT, ResourceOrigin.PLATFORM, OWNER, _fallback_layout))
        self._register_starter_resources(rendering)
        presentation = {"template": "platform.page", "layout": "starter.base", "components": ("starter.header", "starter.footer")}
        rendering.register_operation(PresentationOperation("platform.public.page", OWNER, self._public_page, **presentation))
        rendering.register_operation(PresentationOperation("platform.public.content", OWNER, self._public_content, **presentation))
        rendering.register_operation(PresentationOperation("platform.public.search", OWNER, self._public_search, **presentation))
        self.ready = True
    def shutdown(self) -> None: self.ready = False
    def _register(self, api: APIEngine, name: str, path: str, methods: tuple[str, ...], handler, area: str) -> None:
        target = f"admin.platform.{name}"; action = "view" if area == "diagnostics" else "manage"; resource = f"admin_{area}"
        api.register(RouteDefinition(target, OWNER, RouteType.API, path, methods, target, authentication_required=True, permission=PERMISSIONS[area]), APIOperation(target, OWNER, _any_input, handler, lambda value: value, authorization=lambda request: AuthorizationContext(action, resource, request.authentication)))
    def _content(self, request: APIRequest, data: object) -> object:
        engine = self._service("engine.content", ContentEngine)
        if request.route.method == "GET": return [_content_value(item) for item in engine.query(ContentQuery(page_size=50), request.authentication)]
        if not isinstance(data, dict): raise APIValidationError("Content request is invalid")
        if request.route.method == "DELETE":
            if set(data) != {"id"}: raise APIValidationError("Content request is invalid")
            engine.delete(str(data["id"]), request.authentication)
            self._service("engine.search", SearchEngine).remove("content", str(data["id"]))
            return {"deleted": True}
        if request.route.method == "PATCH":
            if set(data) != {"id", "title", "data", "action"}: raise APIValidationError("Content request is invalid")
            title, content_data = _content_authoring_input(data["title"], data["data"])
            current = engine.get(str(data["id"]), request.authentication)
            action = str(data["action"])
            if action in {"publish", "archive"}:
                self._service("engine.permissions", PermissionEngine).require(
                    CONTENT_PERMISSIONS[action], AuthorizationContext(
                        action, "content", request.authentication, current.content_id,
                        current.owner_user_id))
            if action == "publish": self._ensure_unique_slug(current.content_id, content_data["slug"], request.authentication)
            item = engine.update(str(data["id"]), title=title, data=content_data,
                                 metadata=current.metadata, authentication=request.authentication)
            if action == "publish": item = engine.publish(item.content_id, request.authentication)
            elif action == "archive": item = engine.archive(item.content_id, request.authentication)
            elif action != "save": raise APIValidationError("Content action is invalid")
            self._index_content(item)
            return _content_value(item)
        if set(data) != {"type_id", "title", "data"}: raise APIValidationError("Content request is invalid")
        title, content_data = _content_authoring_input(data["title"], data["data"])
        item = engine.create(str(data["type_id"]), title=title, data=content_data, metadata={}, authentication=request.authentication)
        self._index_content(item)
        return _content_value(item)
    def _content_preview(self, request: APIRequest, data: object) -> object:
        if not isinstance(data, dict) or set(data) != {"title", "data"}:
            raise APIValidationError("Content preview request is invalid")
        title, content_data = _content_authoring_input(data["title"], data["data"])
        model = {"view": "detail", "title": title, "body": content_data["body"], "published_at": ""}
        return {"title": title, "data": dict(content_data), "html": _view_markup(model)}
    def _content_capabilities(self, request: APIRequest, data: object) -> object:
        permissions = self._service("engine.permissions", PermissionEngine)
        return {action: permissions.evaluate(permission_id, AuthorizationContext(
            action, "content", request.authentication)).allowed
            for action, permission_id in CONTENT_PERMISSIONS.items()}
    def _ensure_unique_slug(self, content_id: str, slug: object, authentication) -> None:
        engine = self._service("engine.content", ContentEngine)
        page = 1
        while True:
            items = engine.query(ContentQuery(page=page, page_size=100), authentication)
            if any(item.content_id != content_id and item.state is not ContentState.ARCHIVED
                   and item.data.get("slug") == slug for item in items):
                raise APIValidationError("Content slug is already in use")
            if len(items) < 100: return
            page += 1
    def _media(self, request: APIRequest, data: object) -> object:
        engine = self._service("engine.media", MediaEngine)
        if request.route.method == "GET":
            return [_media_value(item) for item in engine.list(request.authentication)]
        if not isinstance(data, dict) or set(data) != {"file_name", "mime_type", "text"}: raise APIValidationError("Media request is invalid")
        if data["mime_type"] != "text/plain" or not isinstance(data["text"], str):
            raise APIValidationError("Media must be a plain-text document")
        encoded = data["text"].encode("utf-8")
        if not 1 <= len(encoded) <= 10_000:
            raise APIValidationError("Media text must contain between 1 and 10,000 UTF-8 bytes")
        item = engine.upload(media_type=MediaType.DOCUMENT, file_name=str(data["file_name"]), mime_type="text/plain", data=encoded, metadata={}, public=False, authentication=request.authentication)
        return _media_value(item)
    def _settings(self, request: APIRequest, data: object) -> object:
        engine = self._service("engine.settings", SettingsEngine); scope = SettingScope(SettingScopeKind.PLATFORM, OWNER)
        if request.route.method == "PATCH":
            if not isinstance(data, dict) or set(data) != {"value"}: raise APIValidationError("Setting request is invalid")
            result = engine.set("site_title", scope, str(data["value"]), request.authentication)
        else: result = engine.get("site_title", scope, request.authentication)
        return {"key": result.key, "value": result.value, "customized": result.customized}
    def _extensions(self, request: APIRequest, data: object) -> object:
        manager = self._service("core.extensions", ExtensionManager)
        if request.route.method == "POST":
            if not isinstance(data, dict) or set(data) - {"type", "id", "action", "granted_permissions"} or not {"type", "id", "action"}.issubset(data): raise APIValidationError("Extension request is invalid")
            kind, identifier, action = str(data["type"]), str(data["id"]), str(data["action"])
            engine = self._service("engine.plugins", PluginEngine) if kind == "plugin" else self._service("engine.themes", ThemeEngine) if kind == "theme" else None
            if engine is None or action not in {"activate", "deactivate"}: raise APIValidationError("Extension request is invalid")
            if kind == "plugin" and action == "activate" and not engine.is_bound(identifier):
                grants = data.get("granted_permissions")
                if not isinstance(grants, list) or any(not isinstance(item, str) for item in grants):
                    raise APIValidationError("Plugin capabilities must be granted explicitly")
                engine.bind_declarative(identifier, granted_permissions=frozenset(grants))
            success = engine.activate(identifier) if action == "activate" else engine.deactivate(identifier)
            if not success: raise APIValidationError("Extension lifecycle operation failed safely")
        plugins = self._service("engine.plugins", PluginEngine)
        active_theme = self._service("engine.themes", ThemeEngine).active_theme
        return [_extension_value(manager, plugins, identifier, active_theme)
                for identifier in manager.registered()]
    def _diagnostics(self, request: APIRequest, data: object) -> object:
        health = self._service("engine.observability", HealthEngine)
        return {"liveness": health.public_liveness(), "readiness": health.public_readiness(),
                "operations": health.operator_diagnostics()}
    def _dashboard(self, request: APIRequest, data: object) -> object:
        permissions = self._service("engine.permissions", PermissionEngine)
        allowed = {area: permissions.evaluate(permission_id, AuthorizationContext(
            "view" if area == "diagnostics" else "manage", f"admin_{area}", request.authentication)).allowed
            for area, permission_id in PERMISSIONS.items()}
        result: dict[str, object] = {"areas": [area for area in PERMISSIONS if allowed[area]]}
        if allowed["content"]:
            try:
                items = self._service("engine.content", ContentEngine).query(ContentQuery(page_size=100), request.authentication)
                states = {state.value: sum(item.state is state for item in items) for state in ContentState}
                result["content"] = {"count": len(items), **states}
            except Exception: result["content"] = {"count": None}
        if allowed["media"]:
            try: result["media"] = {"count": len(self._service("engine.media", MediaEngine).list(request.authentication))}
            except Exception: result["media"] = {"count": None}
        if allowed["extensions"]:
            manager = self._service("core.extensions", ExtensionManager)
            result["extensions"] = {"installed": len(manager.registered()),
                                    "active_plugins": sum(manager.state(item).value == "enabled" and manager.manifest(item).type.value == "plugin" for item in manager.registered()),
                                    "active_theme": self._service("engine.themes", ThemeEngine).active_theme}
        if allowed["diagnostics"]:
            result["health"] = self._diagnostics(request, data)
        return result
    def _search(self, request: APIRequest, data: object) -> object:
        return [{"id": item.resource_id, "title": item.title, "type": item.resource_type} for item in self._service("engine.search", SearchEngine).query(SearchQuery(text=request.query.get("q", "")), request.authentication)]
    def _localize(self, request: APIRequest, data: object) -> object:
        if set(request.query) - {"locale", "key"}: raise APIValidationError("Localization request is invalid")
        locale = request.query.get("locale", "en")
        fallbacks = () if locale == "en" else ("en",)
        item = self._service("engine.localization", LocalizationEngine).translate(owner=OWNER, namespace="public", key=request.query.get("key", "public.welcome"), locale_id=locale, fallback_locales=fallbacks)
        return {"value": item.value, "locale": item.locale_id, "fallback": item.fallback_used, "missing": not item.resolved}
    def _public_page(self, route) -> object:
        slug = route.parameters["slug"]
        if slug == "content": return self._content_listing()
        matched = None
        try:
            for item in self._service("engine.content", ContentEngine).query(ContentQuery(type_id="page", page_size=100)):
                if item.data.get("slug") == slug:
                    matched = item
                    break
        except Exception:
            # A clean distribution intentionally has no domain Content Type yet.
            pass
        if slug == "welcome":
            listing = self._content_listing()
            return {**listing, "view": "home",
                    "title": matched.title if matched is not None else "Welcome to your site",
                    "body": article_text(str(matched.data.get("body", ""))) if matched is not None else "Your content will appear here once it is published."}
        if matched is not None: return self._detail_model(matched)
        raise RenderResourceNotFound("Public page was not found")

    def _public_content(self, route) -> object:
        try: item = self._service("engine.content", ContentEngine).get(route.parameters["content_id"])
        except Exception as exc: raise RenderResourceNotFound("Public content was not found") from exc
        if item.state is not ContentState.PUBLISHED: raise RenderResourceNotFound("Public content was not found")
        return self._detail_model(item)

    def _public_search(self, route) -> object:
        query = route.parameters["query"].strip()
        try: results = self._service("engine.search", SearchEngine).query(SearchQuery(text=query, page_size=50))
        except Exception as exc: raise RenderResourceNotFound("Search is unavailable") from exc
        return {"view": "search", "title": "Search", "query": query, "results": tuple(
            {"title": item.title, "href": _search_href(item.resource_type, item.resource_id),
             "description": item.description or ""} for item in results)}

    def _content_listing(self) -> dict[str, object]:
        try: items = self._service("engine.content", ContentEngine).query(ContentQuery(state=ContentState.PUBLISHED, page_size=50))
        except Exception: items = ()
        return {"view": "listing", "title": "Published content", "items": tuple(
            {"id": item.content_id, "title": item.title, "summary": article_text(str(item.data.get("body", "")))[:180],
             "published_at": item.published_at or ""} for item in items)}

    @staticmethod
    def _detail_model(item) -> dict[str, object]:
        return {"view": "detail", "id": item.content_id, "title": item.title,
                "body": sanitize_article_html(str(item.data.get("body", ""))), "published_at": item.published_at or ""}

    def _register_starter_resources(self, rendering: RenderingEngine) -> None:
        themes = self._service("engine.themes", ThemeEngine); theme_id = "favorite.theme.starter"
        try: themes.package(theme_id)
        except Exception: return
        for resource_id, kind, reference in (
            ("starter.header", ResourceKind.COMPONENT, "components/header.html"),
            ("starter.footer", ResourceKind.COMPONENT, "components/footer.html"),
            ("platform.page", ResourceKind.TEMPLATE, "templates/page.html"),
            ("starter.base", ResourceKind.LAYOUT, "layouts/base.html"),
        ):
            rendering.register_resource(RenderResource(resource_id, kind, ResourceOrigin.THEME, theme_id,
                _starter_renderer(themes, theme_id, reference), theme_id=theme_id, package_reference=reference))
    def _service(self, name: str, expected):
        if self._container is None: raise RuntimeError("Admin platform is not initialized")
        return self._container.resolve(name, expected)

    def _register_platform_contracts(self, permissions: PermissionEngine) -> None:
        for action, permission_id in CONTENT_PERMISSIONS.items():
            permissions.register(PermissionDefinition(permission_id, OWNER, action, "content", allow_public=action == "read"))
        for action, permission_id in MEDIA_PERMISSIONS.items():
            permissions.register(PermissionDefinition(permission_id, OWNER, action, "media", allow_owner=True, allow_public=action == "read"))
        permissions.register(PermissionDefinition(SETTING_PERMISSIONS["read"], OWNER, "read", "setting"))
        permissions.register(PermissionDefinition(SETTING_PERMISSIONS["write"], OWNER, "update", "setting"))
        content = self._service("engine.content", ContentEngine)
        fields = (ContentField("slug", FieldKind.STRING, True), ContentField("body", FieldKind.STRING, True))
        content.register_type(ContentType("page", OWNER, "Page", fields, CONTENT_PERMISSIONS))
        content.register_type(ContentType("post", OWNER, "Post", fields, CONTENT_PERMISSIONS))
        self._service("engine.media", MediaEngine).register_access(MediaAccessContract(OWNER, MEDIA_PERMISSIONS))
        self._service("engine.settings", SettingsEngine).register(SettingDefinition(
            "site_title", OWNER, SettingScopeKind.PLATFORM, str, default="Favorite CMS",
            read_permission=SETTING_PERMISSIONS["read"], write_permission=SETTING_PERMISSIONS["write"]))
        self._service("engine.search", SearchEngine).register_type(SearchableType(
            "content", OWNER, CONTENT_PERMISSIONS["read"], self._content_visibility))
        localization = self._service("engine.localization", LocalizationEngine)
        localization.register_language(Language("en", "English", "English")); localization.register_language(Language("fr", "French", "Français"))
        localization.register_locale(Locale("en", "en")); localization.register_locale(Locale("fr", "fr")); localization.set_default("en")
        localization.register_translations(TranslationResource(OWNER, "public", "en", {"public.welcome": "Welcome"}))

    def _content_visibility(self, resource_id: str) -> ResourceVisibility:
        try:
            item = self._service("engine.content", ContentEngine).get(resource_id)
            return ResourceVisibility(True, item.state is ContentState.PUBLISHED, item.owner_user_id)
        except Exception:
            return ResourceVisibility(False, False, None)

    def _index_content(self, item) -> None:
        self._service("engine.search", SearchEngine).index(SearchDocument(
            item.content_id, "content", item.title, article_text(str(item.data.get("body", ""))), resource_reference=f"content:{item.content_id}"))

def _any_input(query: Mapping[str, str], body: object) -> object: return body
def _query_only(query: Mapping[str, str], body: object) -> object:
    if body is not None: raise APIValidationError("Request body is unsupported")
    return query
def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, dict): raise APIValidationError("Object value is required")
    return value
def _content_authoring_input(title: object, data: object) -> tuple[str, Mapping[str, object]]:
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 500:
        raise APIValidationError("Content title must contain between 1 and 500 characters")
    values = _mapping(data)
    if set(values) != {"slug", "body"} or not isinstance(values["slug"], str) or not isinstance(values["body"], str):
        raise APIValidationError("Page content fields are invalid")
    slug, body = normalize_slug(values["slug"]), sanitize_article_html(values["body"])
    if not valid_slug(slug):
        raise APIValidationError("Content slug must use Unicode letters, numbers, and single hyphens")
    if not 1 <= len(body) <= 100_000:
        raise APIValidationError("Content body must contain between 1 and 100,000 characters")
    return title.strip(), {"slug": slug, "body": body}
def _content_value(item) -> dict[str, object]: return {"id": item.content_id, "type": item.type_id, "title": item.title, "data": dict(item.data), "state": item.state.value}
def _media_value(item) -> dict[str, object]: return {"id": item.media_id, "name": item.file_name, "mime_type": item.mime_type, "type": item.media_type.value, "size": item.size, "metadata": dict(item.metadata)}

def _extension_value(manager: ExtensionManager, plugins: PluginEngine, identifier: str,
                     active_theme: str | None) -> dict[str, object]:
    manifest = manager.manifest(identifier)
    is_plugin = manifest.type.value == "plugin"
    return {
        "id": identifier,
        "name": manifest.name,
        "version": str(manifest.version),
        "description": manifest.description,
        "author": manifest.author,
        "type": manifest.type.value,
        "state": manager.state(identifier).value,
        "failure": manager.failure(identifier),
        "compatible": manifest.supports_core("0.1.0"),
        "active": manifest.type.value == "theme" and active_theme == identifier,
        "dependencies": dict(manifest.dependencies),
        "optional_dependencies": dict(manifest.optional_dependencies),
        "permissions": list(manifest.permissions),
        "granted_permissions": list(plugins.granted_permissions(identifier)) if is_plugin else [],
    }

def _search_href(resource_type: str, resource_id: str) -> str:
    return f"/site/content/{quote(resource_id, safe='')}" if resource_type == "content" else "/site/content"

def _starter_renderer(themes: ThemeEngine, theme_id: str, reference: str):
    def render(values: Mapping[str, object]) -> str:
        source = themes.resource_text(theme_id, reference)
        model = values.get("model")
        if not isinstance(model, dict): model = {}
        components = values.get("components")
        component_values = components if isinstance(components, Mapping) else {}
        replacements = {
            "{{ title }}": escape(str(model.get("title", "Favorite CMS"))),
            "{{ body }}": str(values.get("body", "")),
            "{{ content }}": _view_markup(model),
            "{{ header }}": str(component_values.get("starter.header", "")),
            "{{ footer }}": str(component_values.get("starter.footer", "")),
            "{{ styles }}": themes.resource_text(theme_id, "assets/starter.css"),
        }
        for token, value in replacements.items(): source = source.replace(token, value)
        return source
    return render

def _view_markup(model: Mapping[str, object]) -> str:
    view = str(model.get("view", "detail"))
    if view == "home":
        cards = _cards(model.get("items"), limit=6)
        return (f'<section class="hero" aria-labelledby="hero-title"><div class="shell hero-grid"><div>'
                f'<p class="eyebrow">A thoughtful home for your content</p><h1 id="hero-title">{escape(str(model.get("title", "Welcome to your site")))}</h1>'
                f'<p class="hero-copy">{escape(str(model.get("body", "Your content will appear here once it is published.")))}</p>'
                f'<div class="actions"><a class="button" href="/site/content">Explore published content</a><a class="text-link" href="#latest">See what is new</a></div></div>'
                f'<aside class="hero-panel" aria-label="Starter Theme overview"><span>Favorite Starter</span><strong>Clear, accessible, ready for your voice.</strong><p>Publish from the CMS and the Theme keeps presentation consistent.</p></aside></div></section>'
                f'<section class="section shell" id="latest" aria-labelledby="latest-title"><div class="section-heading"><div><p class="eyebrow">From your site</p><h2 id="latest-title">Latest published content</h2></div><a class="text-link" href="/site/content">View all content</a></div>{cards}</section>')
    if view == "listing":
        return (f'<section class="page-hero shell"><p class="eyebrow">Library</p><h1>{escape(str(model.get("title", "Published content")))}</h1>'
                f'<p>Browse the resources currently published on this site.</p></section><section class="section shell" aria-label="Published content">{_cards(model.get("items"))}</section>')
    if view == "search":
        query = escape(str(model.get("query", "")))
        results = _search_results(model.get("results"))
        return (f'<section class="page-hero shell"><p class="eyebrow">Search</p><h1>Find published content</h1>'
                f'<form class="search" data-search-form><label for="site-search">Search this site</label><div><input id="site-search" name="q" value="{query}" required maxlength="500"><button class="button" type="submit">Search</button></div></form></section>'
                f'<section class="section shell" aria-live="polite"><h2>Results for “{query}”</h2>{results}</section>')
    title = escape(str(model.get("title", "Content")))
    body = sanitize_article_html(str(model.get("body", "")))
    published = escape(str(model.get("published_at", ""))[:10])
    meta = f'<p class="meta">Published {published}</p>' if published else ""
    return (f'<article class="article shell"><a class="back-link" href="/site/content">← Back to published content</a><header><p class="eyebrow">Published content</p><h1>{title}</h1>{meta}</header>'
            f'<div class="prose">{body or "<p>This resource has no body content yet.</p>"}</div></article>')

def _cards(value: object, *, limit: int | None = None) -> str:
    items = tuple(value) if isinstance(value, (tuple, list)) else ()
    if limit is not None: items = items[:limit]
    if not items:
        return '<div class="empty-state"><strong>Your published content will appear here.</strong><p>Use the CMS to publish your first resource when you are ready.</p></div>'
    cards = []
    for item in items:
        if not isinstance(item, Mapping): continue
        cards.append(f'<article class="content-card"><p class="card-label">Published</p><h3><a href="/site/content/{quote(str(item.get("id", "")), safe="")}">{escape(str(item.get("title", "Untitled")))}</a></h3><p>{escape(str(item.get("summary", ""))) or "Open this resource to read more."}</p><a class="card-link" href="/site/content/{quote(str(item.get("id", "")), safe="")}">Read content <span aria-hidden="true">→</span></a></article>')
    return '<div class="content-grid">' + "".join(cards) + "</div>"

def _search_results(value: object) -> str:
    items = tuple(value) if isinstance(value, (tuple, list)) else ()
    if not items: return '<div class="empty-state"><strong>No matching content found.</strong><p>Try another phrase or browse all published content.</p><a class="text-link" href="/site/content">Browse content</a></div>'
    output = []
    for item in items:
        if not isinstance(item, Mapping): continue
        output.append(f'<li><a href="{escape(str(item.get("href", "/site/content")), quote=True)}"><strong>{escape(str(item.get("title", "Untitled")))}</strong><span>{escape(str(item.get("description", ""))) or "Published content"}</span></a></li>')
    return '<ol class="result-list">' + "".join(output) + "</ol>"

def _fallback_header(values: Mapping[str, object]) -> str:
    return '<header class="site-header"><div class="shell header-row"><a class="brand" href="/site/welcome">Favorite CMS</a><nav aria-label="Primary navigation"><a href="/site/welcome">Home</a><a href="/site/content">Content</a><a href="/site/search/content">Search</a></nav></div></header>'

def _fallback_footer(values: Mapping[str, object]) -> str:
    return '<footer class="site-footer"><div class="shell"><strong>Favorite CMS</strong><p>A flexible foundation for the content you publish.</p></div></footer>'

def _fallback_layout(values: Mapping[str, object]) -> str:
    title = escape(str(values.get("model", {}).get("title", "Favorite CMS"))) if isinstance(values.get("model"), Mapping) else "Favorite CMS"
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><meta name="favorite-renderer" content="backend"></head><body>{values.get("body", "")}</body></html>'

def _page_template(values: Mapping[str, object]) -> str:
    model = values["model"]
    if not isinstance(model, dict): raise APIValidationError("Page model is invalid")
    components = values.get("components")
    resolved = components if isinstance(components, Mapping) else {}
    return str(resolved.get("starter.header", "")) + '<main id="main-content">' + _view_markup(model) + '</main>' + str(resolved.get("starter.footer", ""))
