from __future__ import annotations

from backend.engines.api import APIEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.content import ContentEngine
from backend.engines.permissions import PermissionEngine, RoleGrant
from backend.engines.plugins import PluginEngine
from backend.engines.routing import RoutingEngine
from backend.engines.users import UserEngine
from backend.tests.phase7.conftest import phase7_kernel


SEO_CAPABILITIES = frozenset({"admin.register", "api.register", "content.read", "content.update",
                              "rendering.register", "settings.access"})
CONTACT_CAPABILITIES = frozenset({"admin.register", "api.register", "notification.send",
                                  "rendering.register", "routing.register", "settings.access"})


def _operator(kernel):
    users = kernel.container.resolve("engine.users", UserEngine)
    auth = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    user = users.create(email="phase23@example.test", display_name="Phase 23", role="phase23")
    auth.set_password(user.user_id, "phase twenty three sufficiently long password")
    for permission in ("admin.content.manage", "admin.media.manage", "admin.extensions.manage",
                       "platform.content.create", "platform.content.read", "platform.content.update",
                       "platform.content.publish", "platform.media.create", "platform.media.read"):
        permissions.grant_role(RoleGrant("phase23", permission, "application.admin.platform"))
    result = auth.login(email="phase23@example.test", password="phase twenty three sufficiently long password")
    assert result.token
    return result.token.reveal()


def _services(kernel):
    return (kernel.container.resolve("engine.routing", RoutingEngine),
            kernel.container.resolve("engine.api", APIEngine))


def test_admin_content_edit_preserves_content_owned_seo_metadata(phase7_kernel) -> None:
    credential = _operator(phase7_kernel); routing, api = _services(phase7_kernel)
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    plugins.bind_declarative("favorite.plugin.seo", granted_permissions=SEO_CAPABILITIES)
    assert plugins.activate("favorite.plugin.seo")
    created = api.handle(routing.resolve("POST", "/admin/api/content"), credential=credential,
                         body={"type_id": "page", "title": "Authoring", "data": {"slug": "authoring", "body": "Body"}})
    content_id = created.body["data"]["id"]
    metadata = {"description": "Preserved", "canonical_path": "", "robots": "index,follow",
                "open_graph_title": "", "open_graph_description": "", "open_graph_image": ""}
    assert api.handle(routing.resolve("PATCH", "/api/plugins/seo/content"), credential=credential,
                      body={"content_id": content_id, "metadata": metadata}).status == 200
    edited = api.handle(routing.resolve("PATCH", "/admin/api/content"), credential=credential,
                        body={"id": content_id, "title": "Edited", "data": {"slug": "authoring", "body": "Edited body"}, "action": "save"})
    assert edited.status == 200
    stored = phase7_kernel.container.resolve("engine.content", ContentEngine).get(
        content_id, AuthenticationEngine.resolve(phase7_kernel.container.resolve("engine.authentication", AuthenticationEngine), credential))
    assert stored.metadata["seo"]["description"] == "Preserved"


def test_admin_content_supports_registered_post_type(phase7_kernel) -> None:
    credential = _operator(phase7_kernel); routing, api = _services(phase7_kernel)
    created = api.handle(routing.resolve("POST", "/admin/api/content"), credential=credential,
                         body={"type_id": "post", "title": "First post",
                               "data": {"slug": "first-post", "body": "Post body"}})
    assert created.status == 200
    assert created.body["data"]["type"] == "post"
    listed = api.handle(routing.resolve("GET", "/admin/api/content"), credential=credential)
    assert any(item["id"] == created.body["data"]["id"] and item["type"] == "post"
               for item in listed.body["data"])


def test_post_writes_require_route_and_action_specific_permissions(phase7_kernel) -> None:
    routing, api = _services(phase7_kernel)
    users = phase7_kernel.container.resolve("engine.users", UserEngine)
    auth = phase7_kernel.container.resolve("engine.authentication", AuthenticationEngine)
    permissions = phase7_kernel.container.resolve("engine.permissions", PermissionEngine)

    def credential(role: str) -> str:
        user = users.create(email=f"{role}@example.test", display_name=role, role=role)
        auth.set_password(user.user_id, "a sufficiently long permission password")
        result = auth.login(email=user.email, password="a sufficiently long permission password")
        assert result.token
        return result.token.reveal()

    authorized_role = "post-author"
    for permission in ("admin.content.manage", "platform.content.create", "platform.content.read",
                       "platform.content.update", "platform.content.delete", "platform.content.publish"):
        permissions.grant_role(RoleGrant(authorized_role, permission, "application.admin.platform"))
    authorized = credential(authorized_role)

    created = api.handle(routing.resolve("POST", "/admin/api/content"), credential=authorized,
                         body={"type_id": "post", "title": "Protected post",
                               "data": {"slug": "protected-post", "body": "Draft"}})
    assert created.status == 200
    content_id = created.body["data"]["id"]
    updated = api.handle(routing.resolve("PATCH", "/admin/api/content"), credential=authorized,
                         body={"id": content_id, "title": "Updated post",
                               "data": {"slug": "protected-post", "body": "Updated"}, "action": "save"})
    assert updated.status == 200

    no_publish_role = "post-author-without-publish"
    for permission in ("admin.content.manage", "platform.content.read", "platform.content.update"):
        permissions.grant_role(RoleGrant(no_publish_role, permission, "application.admin.platform"))
    no_publish = credential(no_publish_role)
    denied_publish = api.handle(routing.resolve("PATCH", "/admin/api/content"), credential=no_publish,
                                 body={"id": content_id, "title": "Unauthorized mutation",
                                       "data": {"slug": "protected-post", "body": "Unauthorized mutation"},
                                       "action": "publish"})
    assert denied_publish.status == 403 and denied_publish.body["error"]["code"] == "permission_denied"
    after_denial = api.handle(routing.resolve("GET", "/admin/api/content"), credential=authorized)
    unchanged = next(item for item in after_denial.body["data"] if item["id"] == content_id)
    assert unchanged["title"] == "Updated post" and unchanged["data"]["body"] == "Updated"
    published = api.handle(routing.resolve("PATCH", "/admin/api/content"), credential=authorized,
                           body={"id": content_id, "title": "Updated post",
                                 "data": {"slug": "protected-post", "body": "Updated"}, "action": "publish"})
    assert published.status == 200 and published.body["data"]["state"] == "published"

    no_delete_role = "post-author-without-delete"
    for permission in ("admin.content.manage", "platform.content.read"):
        permissions.grant_role(RoleGrant(no_delete_role, permission, "application.admin.platform"))
    no_delete = credential(no_delete_role)
    denied_delete = api.handle(routing.resolve("DELETE", "/admin/api/content"), credential=no_delete,
                                body={"id": content_id})
    assert denied_delete.status == 403 and denied_delete.body["error"]["code"] == "permission_denied"
    assert api.handle(routing.resolve("DELETE", "/admin/api/content"), credential=authorized,
                      body={"id": content_id}).status == 200

    route_only_role = "post-route-only"
    permissions.grant_role(RoleGrant(route_only_role, "admin.content.manage", "application.admin.platform"))
    route_only = credential(route_only_role)
    denied_create = api.handle(routing.resolve("POST", "/admin/api/content"), credential=route_only,
                                body={"type_id": "post", "title": "Denied",
                                      "data": {"slug": "denied", "body": "Denied"}})
    assert denied_create.status == 403 and denied_create.body["error"]["code"] == "permission_denied"

    action_only_role = "post-action-only"
    permissions.grant_role(RoleGrant(action_only_role, "platform.content.create", "application.admin.platform"))
    action_only = credential(action_only_role)
    denied_route = api.handle(routing.resolve("POST", "/admin/api/content"), credential=action_only,
                               body={"type_id": "post", "title": "Denied",
                                     "data": {"slug": "denied-route", "body": "Denied"}})
    assert denied_route.status == 403 and denied_route.body["error"]["code"] == "permission_denied"


def test_notification_admin_summary_is_redacted_and_permission_protected(phase7_kernel) -> None:
    credential = _operator(phase7_kernel); routing, api = _services(phase7_kernel)
    plugins = phase7_kernel.container.resolve("engine.plugins", PluginEngine)
    plugins.bind_declarative("favorite.plugin.contact", granted_permissions=CONTACT_CAPABILITIES)
    assert plugins.activate("favorite.plugin.contact")
    api.handle(routing.resolve("PATCH", "/api/plugins/contact/settings"), credential=credential,
               body={"recipient": "operator@example.test", "delivery": "pending"})
    api.handle(routing.resolve("POST", "/api/plugins/contact/submissions"),
               body={"name": "Visitor", "email": "visitor@example.test", "message": "Private message", "website": ""})
    response = api.handle(routing.resolve("GET", "/api/plugins/contact/settings"), credential=credential)
    assert response.status == 200 and response.body["data"]["status"] == {
        "pending": 1, "delivered": 0, "failed": 0, "attempts": 0, "provider_available": False}
    assert "visitor@example.test" not in repr(response.body) and "Private message" not in repr(response.body)
    assert api.handle(routing.resolve("GET", "/api/plugins/contact/settings")).status == 401


def test_authoring_and_media_management_limits_fail_safely(phase7_kernel) -> None:
    credential = _operator(phase7_kernel); routing, api = _services(phase7_kernel)
    invalid_content = api.handle(routing.resolve("POST", "/admin/api/content"), credential=credential,
                                 body={"type_id": "page", "title": "Title", "data": {"slug": "../escape", "body": "Body"}})
    invalid_media = api.handle(routing.resolve("POST", "/admin/api/media"), credential=credential,
                               body={"file_name": "safe.txt", "mime_type": "text/html", "text": "<script>"})
    oversized_media = api.handle(routing.resolve("POST", "/admin/api/media"), credential=credential,
                                 body={"file_name": "safe.txt", "mime_type": "text/plain", "text": "x" * 10_001})
    assert invalid_content.status == invalid_media.status == oversized_media.status == 400
    assert "../escape" not in repr(invalid_content.body) and "<script>" not in repr(invalid_media.body)
