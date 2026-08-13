from fastapi.testclient import TestClient

from backend.config import Configuration
from backend.engines.notifications import NotificationEngine
from backend.main import create_app
from backend.operations import HealthEngine
from backend.tests.e2e_app import PASSWORD, seed


def _login(client: TestClient, email: str = "operator@example.test") -> dict[str, str]:
    response = client.post("/admin/api/session", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"authorization": f"Bearer {response.json()['data']['access_token']}"}


def test_private_diagnostics_are_authorized_detailed_and_redacted() -> None:
    app = create_app(on_started=seed)
    with TestClient(app) as client:
        assert client.get("/admin/api/diagnostics").status_code == 401
        assert client.get("/admin/api/diagnostics", headers=_login(client, "viewer@example.test")).status_code == 403
        response = client.get("/admin/api/diagnostics", headers=_login(client))
        assert response.status_code == 200
        data = response.json()["data"]
        assert set(data["liveness"]) == {"status", "live"}
        assert set(data["readiness"]) == {"status", "ready"}
        operations = data["operations"]
        assert operations["version"] == "0.1.0"
        assert operations["migration"]["mode"] == "explicit"
        assert operations["installation"]["automatic_install"] is False
        assert operations["installation"]["automatic_migration"] is False
        assert operations["update"]["remote_updates"] is False
        assert operations["recovery"]["native_postgresql_restore"] is False
        rendered = str(data).casefold()
        for forbidden in ("sqlite+pysqlite", "signing-secret", "storage/e2e", "password", "traceback", "sqlalchemy"):
            assert forbidden not in rendered


def test_public_health_stays_minimal_and_errors_keep_stable_identifiers() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        assert set(client.get("/health/live").json()["data"]) == {"status", "live"}
        assert set(client.get("/health/ready").json()["data"]) == {"status", "ready"}
        unauthorized = client.get("/admin/api/diagnostics").json()
        assert unauthorized["error"]["code"] == "authentication_required"
        assert unauthorized["request_id"] and unauthorized["error"]["error_id"]
        invalid = client.post("/admin/api/media", headers=_login(client), json={"file_name": "../secret", "mime_type": "text/plain", "text": "x"}).json()
        assert invalid["error"]["code"] == "validation_error"
        assert "../" not in str(invalid)


def test_owner_status_contracts_expose_metadata_not_values() -> None:
    app = create_app(on_started=seed)
    with TestClient(app):
        kernel = app.state.kernel
        configuration = kernel.container.resolve("core.configuration", Configuration)
        assert configuration.is_configured("database.url")
        assert configuration.is_configured("authentication.jwt_secret") is False
        assert "database.url" not in configuration.snapshot()
        health = kernel.container.resolve("engine.observability", HealthEngine)
        diagnostics = health.operator_diagnostics()
        assert diagnostics["notification"]["status"] in {"healthy", "not_configured"}
        assert diagnostics["media"] == {"status": "healthy", "supported": "text_document"}
        notification = kernel.container.resolve("engine.notifications", NotificationEngine).operational_status()
        assert not ({"recipient", "payload", "adapter", "credentials"} & set(notification))


def test_dashboard_includes_status_only_for_diagnostics_permission() -> None:
    with TestClient(create_app(on_started=seed)) as client:
        operator = client.get("/admin/api/dashboard", headers=_login(client)).json()["data"]
        assert operator["health"]["operations"]["configuration"]["database"] == "configured"
        assert operator["health"]["operations"]["migration"]["pending"] == 0
        viewer = client.get("/admin/api/dashboard", headers=_login(client, "viewer@example.test")).json()["data"]
        assert viewer == {"areas": []}
