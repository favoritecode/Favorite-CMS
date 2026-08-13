from fastapi.testclient import TestClient

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
        assert isinstance(operator["media"]["count"], int)
        assert isinstance(operator["health"]["readiness"]["ready"], bool)
        assert operator["extensions"]["active_theme"] is None or isinstance(operator["extensions"]["active_theme"], str)
        viewer = client.get("/admin/api/dashboard", headers=_login(client, "viewer@example.test")).json()["data"]
        assert viewer == {"areas": []}


def test_content_edit_publish_delete_and_media_listing_use_engine_contracts() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        headers = _login(client)
        created = client.post("/admin/api/content", headers=headers, json={
            "type_id": "page", "title": "Draft", "data": {"slug": "phase-16", "body": "Initial"}
        })
        assert created.status_code == 200 and created.json()["data"]["state"] == "draft"
        content_id = created.json()["data"]["id"]
        published = client.patch("/admin/api/content", headers=headers, json={
            "id": content_id, "title": "Edited", "data": {"slug": "phase-16", "body": "Updated"}, "action": "publish"
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
