from fastapi.testclient import TestClient
from uuid import uuid4
import base64

from backend.main import create_app
from backend.tests.e2e_app import PASSWORD, seed


def _login(client: TestClient, email: str = "operator@example.test") -> dict[str, str]:
    response = client.post("/admin/api/session", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_dashboard_is_authenticated_and_permission_filtered() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        assert client.get("/admin/api/dashboard").status_code == 401
        operator = client.get("/admin/api/dashboard", headers=_login(client)).json()["data"]
        assert operator["content"]["count"] >= 1
        assert operator["content"]["published"] >= 1
        assert operator["content"]["draft"] >= 0
        assert isinstance(operator["media"]["count"], int)
        assert isinstance(operator["health"]["readiness"]["ready"], bool)
        assert operator["extensions"]["active_theme"] is None or isinstance(operator["extensions"]["active_theme"], str)
        viewer = client.get("/admin/api/dashboard", headers=_login(client, "viewer@example.test")).json()["data"]
        assert viewer == {"areas": []}


def test_content_edit_publish_delete_and_media_listing_use_engine_contracts() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        headers = _login(client)
        slug = f"phase-16-{uuid4().hex}"
        created = client.post("/admin/api/content", headers=headers, json={
            "type_id": "page", "title": "Draft", "data": {"slug": slug, "body": "Initial"}
        })
        assert created.status_code == 200 and created.json()["data"]["state"] == "draft"
        content_id = created.json()["data"]["id"]
        published = client.patch("/admin/api/content", headers=headers, json={
            "id": content_id, "title": "Edited", "data": {"slug": slug, "body": "Updated"}, "action": "publish"
        })
        assert published.status_code == 200 and published.json()["data"]["state"] == "published"
        uploaded = client.post("/admin/api/media", headers=headers, json={
            "file_name": "phase16.txt", "mime_type": "text/plain", "text": "safe media"
        })
        assert uploaded.status_code == 200
        listing = client.get("/admin/api/media", headers=headers).json()["data"]
        assert any(item == {"id": uploaded.json()["data"]["id"], "name": "phase16.txt", "mime_type": "text/plain", "type": "document", "size": 10, "metadata": {}} for item in listing)
        assert "storage" not in str(listing).lower()
        deleted = client.request("DELETE", "/admin/api/content", headers=headers, json={"id": content_id})
        assert deleted.status_code == 200 and deleted.json()["data"] == {"deleted": True}


def test_featured_image_is_content_owned_validated_and_rendered_safely() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        headers = _login(client)
        slug = f"featured-post-{uuid4().hex}"
        invalid = client.post("/admin/api/content", headers=headers, json={
            "type_id": "post", "title": "Unsafe image", "data": {
                "slug": "unsafe-featured-image", "body": "Body", "featured_image": "javascript:alert(1)"
            },
        })
        assert invalid.status_code == 400

        created = client.post("/admin/api/content", headers=headers, json={
            "type_id": "post", "title": "Featured post", "data": {
                "slug": slug, "body": "Safe article body",
                "featured_image": "https://images.example.test/cover.jpg?size=large&mode=safe",
            },
        })
        assert created.status_code == 200
        content_id = created.json()["data"]["id"]
        published = client.patch("/admin/api/content", headers=headers, json={
            "id": content_id, "title": "Featured post", "data": created.json()["data"]["data"],
            "action": "publish",
        })
        assert published.status_code == 200
        preview = client.post("/admin/api/content/preview", headers=headers, json={
            "title": "Featured post", "data": published.json()["data"]["data"],
        })
        assert preview.status_code == 200
        markup = preview.json()["data"]["html"]
        assert 'src="https://images.example.test/cover.jpg?size=large&amp;mode=safe"' in markup
        assert "javascript:" not in markup


def test_labels_seo_and_visibility_are_content_owned_and_fail_closed() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        headers = _login(client)
        created = client.post("/admin/api/content", headers=headers, json={
            "type_id": "post", "title": "Visibility contract", "data": {
                "slug": f"visibility-{uuid4().hex}", "body": "Bounded body",
                "labels": ["Release", "Guide"], "visibility": "unlisted",
            },
        })
        assert created.status_code == 200
        item = created.json()["data"]
        seo = client.patch("/admin/api/content/seo", headers=headers, json={
            "content_id": item["id"], "metadata": {
                "title": "Search title", "description": "Meta description", "canonical_path": "",
                "robots": "index,follow", "open_graph_title": "", "open_graph_description": "",
                "open_graph_image": "",
            },
        })
        assert seo.status_code == 200 and seo.json()["data"]["metadata"]["description"] == "Meta description"
        published = client.patch("/admin/api/content", headers=headers, json={
            "id": item["id"], "title": item["title"], "data": item["data"], "action": "publish",
        })
        assert published.status_code == 200 and published.json()["data"]["visibility"] == "unlisted"
        assert item["id"] not in client.get("/site/content").text
        assert "Visibility contract" not in client.get("/site/search/Visibility").text

        private_data = {**published.json()["data"]["data"], "visibility": "private"}
        made_private = client.patch("/admin/api/content", headers=headers, json={
            "id": item["id"], "title": item["title"], "data": private_data, "action": "save",
        })
        assert made_private.status_code == 200
        assert client.get(f"/site/content/{item['id']}").status_code == 404

        draft = client.patch("/admin/api/content", headers=headers, json={
            "id": item["id"], "title": item["title"], "data": private_data, "action": "unpublish",
        })
        assert draft.status_code == 200 and draft.json()["data"]["state"] == "draft"


def test_media_accepts_bounded_description_labels_and_visibility_metadata() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        headers = _login(client)
        response = client.post("/admin/api/media", headers=headers, json={
            "file_name": "tagged.txt", "mime_type": "text/plain", "text": "safe",
            "description": "Media description", "labels": ["Docs", "Release"], "visibility": "private",
        })
        assert response.status_code == 200
        metadata = response.json()["data"]["metadata"]
        assert metadata == {"description": "Media description", "labels": ["Docs", "Release"], "visibility": "private"}
        invalid = client.post("/admin/api/media", headers=headers, json={
            "file_name": "bad.txt", "mime_type": "text/plain", "text": "safe",
            "description": "", "labels": ["x" * 41], "visibility": "published",
        })
        assert invalid.status_code == 400


def test_bounded_image_upload_uses_media_storage_and_safe_binary_delivery() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        headers = _login(client)
        # Signature-level transport fixture; production accepts only bounded PNG/JPEG/WebP signatures.
        png = b"\x89PNG\r\n\x1a\n" + b"bounded-image-data"
        uploaded = client.post("/admin/api/media", headers=headers, json={
            "file_name": "cover.png", "mime_type": "image/png",
            "data_base64": base64.b64encode(png).decode("ascii"), "description": "Cover",
            "labels": ["cover"], "visibility": "published",
        })
        assert uploaded.status_code == 200
        media_id = uploaded.json()["data"]["id"]
        delivered = client.get(f"/media/{media_id}")
        assert delivered.status_code == 200 and delivered.content == png
        assert delivered.headers["content-type"].startswith("image/png")
        assert delivered.headers["x-content-type-options"] == "nosniff"
        rejected = client.post("/admin/api/media", headers=headers, json={
            "file_name": "unsafe.svg", "mime_type": "image/svg+xml",
            "data_base64": base64.b64encode(b"<svg><script/></svg>").decode("ascii"),
            "description": "", "labels": [], "visibility": "published",
        })
        assert rejected.status_code == 400
