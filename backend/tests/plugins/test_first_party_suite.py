from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.core.extensions import ExtensionState, ManifestValidationError
from backend.engines.api import APIEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.permissions import PermissionEngine, RoleGrant
from backend.engines.plugins import PluginEngine
from backend.engines.plugins.first_party import load_first_party_runtime
from backend.engines.rendering import RenderingEngine
from backend.engines.rendering import PresentationDecorator
from backend.engines.routing import RouteNotFound, RoutingEngine
from backend.engines.themes import ThemeEngine
from backend.engines.users import UserEngine
from backend.tests.phase7.conftest import phase7_kernel

PLUGINS = {
    "favorite.plugin.seo": frozenset({"admin.register", "api.register", "content.read", "content.update", "rendering.register", "settings.access"}),
    "favorite.plugin.contact": frozenset({"admin.register", "api.register", "notification.send", "rendering.register", "routing.register", "settings.access"}),
    "favorite.plugin.sitemap": frozenset({"admin.register", "api.register", "content.read", "rendering.register", "routing.register", "settings.access"}),
    "favorite.plugin.analytics": frozenset({"admin.register", "api.register", "rendering.register", "settings.access"}),
}

def _credential(kernel) -> str:
    users = kernel.container.resolve("engine.users", UserEngine); auth = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    user = users.create(email="suite@example.test", display_name="Suite Operator", role="suite-operator")
    auth.set_password(user.user_id, "a sufficiently long suite password")
    permissions.grant_role(RoleGrant("suite-operator", "admin.extensions.manage", "application.admin.platform"))
    result = auth.login(email="suite@example.test", password="a sufficiently long suite password"); assert result.token
    return result.token.reveal()

def test_suite_manifests_capabilities_activation_api_rendering_and_cleanup(phase7_kernel) -> None:
    assert phase7_kernel.container.resolve("engine.themes", ThemeEngine).activate("favorite.theme.starter")
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    api = phase7_kernel.container.resolve("engine.api", APIEngine); rendering = phase7_kernel.container.resolve("engine.rendering", RenderingEngine)
    credential = _credential(phase7_kernel)
    for identifier, capabilities in PLUGINS.items():
        manifest = plugins.manifest(identifier)
        assert manifest.version == "1.0.0" and frozenset(manifest.permissions) == capabilities
        with pytest.raises(ManifestValidationError): plugins.bind_declarative(identifier, granted_permissions=frozenset())
        plugins.bind_declarative(identifier, granted_permissions=capabilities); assert plugins.activate(identifier)
    seo = api.handle(routing.resolve("PATCH", "/api/plugins/seo/settings"), credential=credential,
        body={"site_title":"Suite Site","description":"Safe metadata","canonical_base":"https://example.test","robots":"index,follow"})
    assert seo.status == 200
    analytics = api.handle(routing.resolve("PATCH", "/api/plugins/analytics/settings"), credential=credential,
        body={"provider":"first-party","site_id":"suite_site"}); assert analytics.status == 200
    contact = api.handle(routing.resolve("POST", "/api/plugins/contact/submissions"),
        body={"name":"Visitor","email":"visitor@example.test","message":"A valid message","website":""})
    assert contact.status == 201 and contact.body["data"]["status"] == "pending"
    assert api.handle(routing.resolve("POST", "/api/plugins/contact/submissions"),
        body={"name":"Bot","email":"bot@example.test","message":"spam","website":"filled"}).status == 400
    configured_sitemap = api.handle(routing.resolve("PATCH", "/api/plugins/sitemap/settings"), credential=credential,
        body={"base_url":"https://example.test"}); assert configured_sitemap.status == 200
    contact_page = rendering.render(routing.resolve("GET", "/contact")); assert contact_page.status == 200 and "contact-form" in contact_page.body
    sitemap = rendering.render(routing.resolve("GET", "/sitemap.xml")); assert sitemap.status == 200 and sitemap.content_type.startswith("application/xml")
    homepage = rendering.render(routing.resolve("GET", "/site/welcome"))
    assert 'name="description" content="Safe metadata"' in homepage.body and 'name="favorite-analytics"' in homepage.body
    for identifier in reversed(tuple(PLUGINS)):
        assert plugins.deactivate(identifier)
    for path in ("/contact", "/sitemap.xml", "/api/plugins/seo/settings", "/api/plugins/sitemap/settings", "/api/plugins/analytics/settings"):
        with pytest.raises(RouteNotFound): routing.resolve("GET", path)
    clean = rendering.render(routing.resolve("GET", "/site/welcome"))
    assert "favorite-analytics" not in clean.body and "Safe metadata" not in clean.body
    plugins.bind_declarative("favorite.plugin.seo", granted_permissions=PLUGINS["favorite.plugin.seo"])
    assert plugins.activate("favorite.plugin.seo")
    restored = api.handle(routing.resolve("GET", "/api/plugins/seo/settings"), credential=credential)
    assert restored.status == 200 and restored.body["data"]["description"] == "Safe metadata"

def test_suite_permission_denial_and_malicious_configuration_fail_closed(phase7_kernel) -> None:
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine); routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine); api = phase7_kernel.container.resolve("engine.api", APIEngine)
    for identifier in ("favorite.plugin.seo", "favorite.plugin.analytics"):
        plugins.bind_declarative(identifier, granted_permissions=PLUGINS[identifier]); assert plugins.activate(identifier)
    assert api.handle(routing.resolve("GET", "/api/plugins/seo/settings")).status == 401
    credential = _credential(phase7_kernel)
    assert api.handle(routing.resolve("PATCH", "/api/plugins/seo/settings"), credential=credential,
        body={"site_title":"X","description":"","canonical_base":"javascript:alert(1)","robots":"index,follow"}).status == 400
    assert api.handle(routing.resolve("PATCH", "/api/plugins/analytics/settings"), credential=credential,
        body={"provider":"https://evil.example/script.js","site_id":"x"}).status == 400

def test_first_party_packages_are_data_only_and_distribution_safe() -> None:
    for identifier in PLUGINS:
        root = Path("plugins") / identifier
        assert {path.name for path in root.iterdir()} == {"plugin.json", "contributions.json", "README.md"}
        manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8")); assert manifest["id"] == identifier
    source = Path("backend/engines/plugins/first_party.py").read_text(encoding="utf-8")
    for prohibited in ("sqlalchemy", "DatabaseEngine", "StorageProvider", "os.getenv", "os.environ", "subprocess", "os.system", "importlib", "eval(", "exec("):
        assert prohibited not in source

def test_failed_suite_candidate_rolls_back_without_losing_active_seo(tmp_path: Path, phase7_kernel) -> None:
    identifier = "favorite.plugin.seo"; plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    plugins.bind_declarative(identifier, granted_permissions=PLUGINS[identifier]); assert plugins.activate(identifier)
    package = tmp_path / "candidate"; package.mkdir()
    (package / "contributions.json").write_text(json.dumps({"schemaVersion":1,"kind":"seo","title":"Broken SEO","activation":"fail"}), encoding="utf-8")
    runtime = load_first_party_runtime(package, identifier)
    raw = json.loads(Path(f"plugins/{identifier}/plugin.json").read_text(encoding="utf-8")); raw["version"] = "1.1.0"
    from backend.core.extensions import ExtensionManifest
    assert not plugins.update(identifier, ExtensionManifest.from_mapping(raw), runtime, granted_permissions=PLUGINS[identifier])
    assert phase7_kernel.extensions.state(identifier) is ExtensionState.ENABLED
    routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    assert routing.resolve("GET", "/site/welcome").owner == "application.admin.platform"

def test_failing_plugin_decorator_is_isolated_from_theme_rendering(phase7_kernel) -> None:
    assert phase7_kernel.container.resolve("engine.themes", ThemeEngine).activate("favorite.theme.starter")
    rendering = phase7_kernel.container.resolve("engine.rendering", RenderingEngine)
    rendering.for_plugin("favorite.plugin.failing-view").register_decorator(PresentationDecorator(
        "favorite.plugin.failing-view.head", "favorite.plugin.failing-view", lambda body, route, model: (_ for _ in ()).throw(RuntimeError("failure"))))
    response = rendering.render(phase7_kernel.container.resolve("engine.routing", RoutingEngine).resolve("GET", "/site/welcome"))
    assert response.status == 200 and "Favorite Starter" in response.body
