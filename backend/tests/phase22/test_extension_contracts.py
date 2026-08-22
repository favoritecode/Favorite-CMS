from __future__ import annotations

import pytest

from backend.bootstrap import build_kernel
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.api import APIEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.content import ContentEngine, ContentSeoMetadata
from backend.engines.content.engine import InvalidContent
from backend.engines.notifications import (DeliveryStatus, NotificationContract, NotificationEngine,
                                           NotificationRecipient)
from backend.engines.permissions import PermissionEngine, RoleGrant
from backend.engines.plugins import PluginEngine
from backend.engines.rendering import RenderingEngine
from backend.engines.routing import RoutingEngine
from backend.engines.users import UserEngine
from backend.engines.themes import ThemeEngine
from backend.tests.phase7.conftest import phase7_kernel


SEO_CAPABILITIES = frozenset({"admin.register", "api.register", "content.read", "content.update",
                              "rendering.register", "settings.access"})
CONTACT_CAPABILITIES = frozenset({"admin.register", "api.register", "notification.send",
                                  "rendering.register", "routing.register", "settings.access"})


def _operator(kernel):
    users = kernel.container.resolve("engine.users", UserEngine)
    auth = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    user = users.create(email="phase22@example.test", display_name="Phase 22", role="phase22")
    auth.set_password(user.user_id, "phase twenty two sufficiently long password")
    for permission in ("admin.extensions.manage", "platform.content.create", "platform.content.read",
                       "platform.content.update", "platform.content.publish"):
        permissions.grant_role(RoleGrant("phase22", permission, "application.admin.platform"))
    result = auth.login(email="phase22@example.test", password="phase twenty two sufficiently long password")
    assert result.token
    return result.context, result.token.reveal()


def test_content_owned_seo_projection_is_safe_and_public_only(phase7_kernel) -> None:
    context, _ = _operator(phase7_kernel)
    content = phase7_kernel.container.resolve("engine.content", ContentEngine)
    item = content.create("page", title='<Unsafe "Title">', data={"slug": "seo-page", "body": "Default body"},
                          metadata={}, authentication=context)
    content.set_seo_metadata(item.content_id, ContentSeoMetadata(
        title="Search result title", description='<script>alert("x")</script>', canonical_path=f"/site/content/{item.content_id}",
        robots="noindex,nofollow", open_graph_title='OG <Title>',
        open_graph_description='OG "Description"', open_graph_image="/media/preview.png"), context)
    assert content.seo_projection(item.content_id, public_origin="https://example.test") is None
    content.publish(item.content_id, context)
    projection = content.seo_projection(item.content_id, public_origin="https://example.test")
    assert projection and projection.canonical == f"https://example.test/site/content/{item.content_id}"
    assert projection.title == "Search result title"
    assert projection.open_graph_image == "https://example.test/media/preview.png"
    with pytest.raises(InvalidContent):
        content.seo_projection(item.content_id, public_origin="file:///private")
    with pytest.raises(InvalidContent):
        content.set_seo_metadata(item.content_id, ContentSeoMetadata(canonical_path="../escape"), context)


def test_seo_plugin_consumes_projection_and_escapes_output(phase7_kernel) -> None:
    context, credential = _operator(phase7_kernel)
    assert phase7_kernel.container.resolve("engine.themes", ThemeEngine).activate("favorite.theme.starter")
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    plugins.bind_declarative("favorite.plugin.seo", granted_permissions=SEO_CAPABILITIES)
    assert plugins.activate("favorite.plugin.seo")
    content = phase7_kernel.container.resolve("engine.content", ContentEngine)
    item = content.create("page", title="Projected", data={"slug": "projected", "body": "Body"}, metadata={}, authentication=context)
    content.publish(item.content_id, context)
    routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    api = phase7_kernel.container.resolve("engine.api", APIEngine)
    response = api.handle(routing.resolve("PATCH", "/api/plugins/seo/settings"), credential=credential,
                          body={"site_title": "Site", "description": "", "canonical_base": "https://example.test", "robots": "index,follow"})
    assert response.status == 200
    response = api.handle(routing.resolve("PATCH", "/api/plugins/seo/content"), credential=credential,
                          body={"content_id": item.content_id, "metadata": {"title": "SEO <Title>", "description": "A & B", "canonical_path": "",
                              "robots": "index,follow", "open_graph_title": 'A "title"',
                              "open_graph_description": "A <description>", "open_graph_image": ""}})
    assert response.status == 200
    html = phase7_kernel.container.resolve("engine.rendering", RenderingEngine).render(
        routing.resolve("GET", f"/site/content/{item.content_id}")).body
    assert 'content="A &amp; B"' in html and 'content="A &quot;title&quot;"' in html
    assert "<title>SEO &lt;Title&gt;</title>" in html
    assert "<description>" not in html


def test_contact_uses_notification_owner_and_no_provider_stays_pending(phase7_kernel) -> None:
    _, credential = _operator(phase7_kernel)
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    plugins.bind_declarative("favorite.plugin.contact", granted_permissions=CONTACT_CAPABILITIES)
    assert plugins.activate("favorite.plugin.contact")
    routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    api = phase7_kernel.container.resolve("engine.api", APIEngine)
    configured = api.handle(routing.resolve("PATCH", "/api/plugins/contact/settings"), credential=credential,
                            body={"recipient": "recipient@example.test", "delivery": "pending"})
    assert configured.status == 200
    submitted = api.handle(routing.resolve("POST", "/api/plugins/contact/submissions"),
                           body={"name": "Visitor", "email": "visitor@example.test", "message": "Hello", "website": ""})
    assert submitted.status == 201 and submitted.body["data"]["status"] == "pending"
    notifications = phase7_kernel.container.resolve("engine.notifications", NotificationEngine)
    queued = notifications.for_recipient("recipient@example.test", "contact-recipient")
    assert len(queued) == 1 and notifications.result(queued[0].notification_id).status is DeliveryStatus.PENDING
    assert not notifications.adapter_available("email")
    assert plugins.deactivate("favorite.plugin.contact")
    plugins.bind_declarative("favorite.plugin.contact", granted_permissions=CONTACT_CAPABILITIES)
    assert plugins.activate("favorite.plugin.contact")


def test_notification_delivery_state_is_restored_through_settings(tmp_path, monkeypatch) -> None:
    database = tmp_path / "notifications.db"
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{database}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-twenty-two-test-signing-key-at-least-thirty-two-bytes")
    first = build_kernel(); first.bootstrap()
    migrations = first.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade()
    notifications = first.container.resolve("engine.notifications", NotificationEngine)
    notifications.register_contract(NotificationContract(
        "test.phase22.delivery", "test.phase22", lambda payload: None, lambda recipient: None,
        frozenset({"email"}),
    ))
    created = notifications.create(
        "test.phase22.delivery", "test.phase22",
        NotificationRecipient("recipient", "test", "recipient@example.test"),
        "email", {"body": "bounded"},
    )
    first.shutdown()
    second = build_kernel(); second.bootstrap()
    migrations = second.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade()
    restored = second.container.resolve("engine.notifications", NotificationEngine).result(created.notification_id)
    assert restored.status is DeliveryStatus.PENDING and restored.attempts == 0
    second.shutdown()


def test_admin_extension_projection_reports_required_and_granted_capabilities(phase7_kernel) -> None:
    _, credential = _operator(phase7_kernel)
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    plugins.bind_declarative("favorite.plugin.seo", granted_permissions=SEO_CAPABILITIES)
    assert plugins.activate("favorite.plugin.seo")
    routing = phase7_kernel.container.resolve("engine.routing", RoutingEngine)
    response = phase7_kernel.container.resolve("engine.api", APIEngine).handle(
        routing.resolve("GET", "/admin/api/extensions"), credential=credential)
    assert response.status == 200
    seo = next(item for item in response.body["data"] if item["id"] == "favorite.plugin.seo")
    assert set(seo["permissions"]) == SEO_CAPABILITIES
    assert set(seo["granted_permissions"]) == SEO_CAPABILITIES
    assert seo["compatible"] is True and seo["failure"] is None
    assert seo["description"]
    assert isinstance(seo["dependencies"], dict)
    assert isinstance(seo["optional_dependencies"], dict)
