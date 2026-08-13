from fastapi.testclient import TestClient
from backend.core import Kernel
from backend.engines.api import APIEngine, APIOperation, APIValidationError
from backend.engines.routing import RouteDefinition, RouteType
from backend.main import create_app

def test_http_routes_through_routing_then_api(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'http.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "http-test-signing-key-with-at-least-thirty-two-bytes")
    app = create_app()
    with TestClient(app) as client:
        kernel: Kernel = app.state.kernel; api = kernel.container.resolve("engine.api", APIEngine)
        route = RouteDefinition("tests.http.echo", "engine.content", RouteType.API, "/api/echo", ("POST",), "tests.http.echo")
        api.register(route, APIOperation("tests.http.echo", "engine.content",
            lambda query, body: body if isinstance(body, dict) else (_ for _ in ()).throw(APIValidationError("Invalid body")),
            lambda request, value: {"echo": value.get("message")}, lambda value: value))
        response = client.post("/api/echo", json={"message": "hello"})
        assert response.status_code == 200 and response.json()["data"] == {"echo": "hello"}
        assert client.get("/api/echo").status_code == 405
        assert client.get("/not-registered").status_code == 404
        malformed = client.post("/api/echo", content="{broken", headers={"content-type": "application/json"})
        assert malformed.status_code == 400 and "broken" not in malformed.text
