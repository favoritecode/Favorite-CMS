from fastapi.testclient import TestClient

from backend.main import create_app


def test_backend_skeleton_starts() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] == {"name": "Favorite CMS", "status": "ready"}
    assert isinstance(payload["request_id"], str)
