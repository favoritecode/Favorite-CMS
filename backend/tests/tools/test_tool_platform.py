from fastapi.testclient import TestClient
from pathlib import Path
import pytest

from backend.core import Kernel
from backend.engines.authentication import AuthenticationEngine
from backend.engines.content import ContentEngine
from backend.engines.permissions import PermissionDefinition, PermissionEngine
from backend.engines.tools import ToolContract, ToolEngine, ToolFieldKind, ToolInputField, ToolJobStatus, ToolWorkerState, ToolWorkerSubmission
from backend.main import create_app
from backend.tests.e2e_app import PASSWORD, seed


class PublicWorker:
    def healthcheck(self): return True
    def submit(self, tool_id, job_id, values): return ToolWorkerSubmission(f"public:{job_id}", ToolJobStatus.PENDING)
    def state(self, external_id): return ToolWorkerState(ToolJobStatus.RUNNING, 25)
    def cancel(self, external_id): return True

_content_id = ""


def seed_tool(kernel: Kernel) -> None:
    global _content_id
    seed(kernel); owner = "favorite.plugin.public-tool"; permission = "favorite.tool.public.execute"
    kernel.container.resolve("engine.permissions", PermissionEngine).register(PermissionDefinition(permission, owner, "execute", "plugin_tool", allow_public=True))
    tools = kernel.container.resolve("engine.tools", ToolEngine); tools.register_provider("default", PublicWorker())
    tools.for_plugin(owner).register(ToolContract("favorite.tool.public", owner, "Public tool", "A safely rendered Tool form.",
        (ToolInputField("source", ToolFieldKind.URL, True, 500),), permission, public=True))
    auth = kernel.container.resolve("engine.authentication", AuthenticationEngine).login(email="operator@example.test", password=PASSWORD)
    assert auth.token is not None; context = kernel.container.resolve("engine.authentication", AuthenticationEngine).resolve(auth.token.reveal())
    content = kernel.container.resolve("engine.content", ContentEngine)
    page = content.create("page", title="Tool page", data={"slug": "tool-page", "body": '<p>[favorite-tool id="favorite.tool.public"]</p>'}, metadata={}, authentication=context)
    content.publish(page.content_id, context)
    _content_id = page.content_id


def test_public_shortcode_and_generic_tool_api_use_real_routing_permission_and_worker_contracts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test"); monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'tool-platform.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage")); monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "tool-platform-signing-key-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")
    with TestClient(create_app(on_started=seed_tool)) as client:
        page = client.get(f"/site/content/{_content_id}")
        assert page.status_code == 200 and "Public tool" in page.text and "data-tool-form" in page.text
        rejected = client.post("/api/tools/favorite.tool.public/jobs", json={"source": "file:///etc/passwd"})
        assert rejected.status_code == 400
        submitted = client.post("/api/tools/favorite.tool.public/jobs", json={"source": "https://example.test/input"})
        assert submitted.status_code == 202 and submitted.json()["data"]["status"] == "pending"
        job_id = submitted.json()["data"]["id"]
        status = client.get(f"/api/tools/favorite.tool.public/jobs/{job_id}")
        assert status.status_code == 200 and status.json()["data"]["progress"] == 25
