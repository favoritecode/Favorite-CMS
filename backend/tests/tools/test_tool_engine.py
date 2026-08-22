from pathlib import Path

import pytest

from backend.bootstrap import build_kernel
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.authentication import AuthenticationEngine
from backend.engines.permissions import PermissionDefinition, PermissionEngine, RoleGrant
from backend.engines.tools import (InvalidTool, ToolContract, ToolEngine, ToolError, ToolFieldKind, ToolInputField,
    ToolJobStatus, ToolWorkerState, ToolWorkerSubmission)
from backend.engines.users import UserEngine


OWNER = "favorite.plugin.ocr"
PERMISSION = "favorite.tool.ocr.execute"


class Worker:
    def __init__(self) -> None: self.jobs: dict[str, ToolWorkerState] = {}; self.inputs: list[dict[str, object]] = []
    def healthcheck(self) -> bool: return True
    def submit(self, tool_id, job_id, values):
        self.inputs.append(dict(values)); external = f"worker:{job_id}"; self.jobs[external] = ToolWorkerState(ToolJobStatus.RUNNING, 10)
        return ToolWorkerSubmission(external, ToolJobStatus.RUNNING)
    def state(self, external_id): return self.jobs[external_id]
    def cancel(self, external_id): self.jobs[external_id] = ToolWorkerState(ToolJobStatus.CANCELLED); return True


def _contract() -> ToolContract:
    return ToolContract("favorite.tool.ocr", OWNER, "OCR", "Extract text from an approved Media resource.", (
        ToolInputField("media_id", ToolFieldKind.MEDIA, True), ToolInputField("language", ToolFieldKind.SELECT, True, choices=("eng", "ben")),
    ), PERMISSION)


def _kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FAVORITE_ENV", "test"); monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'tools.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage")); monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "tool-test-signing-key-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")
    first = build_kernel(); first.bootstrap(); migrations = first.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade(); first.shutdown()
    kernel = build_kernel(); kernel.bootstrap(); permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
    permissions.register(PermissionDefinition(PERMISSION, OWNER, "execute", "plugin_tool")); permissions.grant_role(RoleGrant("tool-user", PERMISSION, OWNER))
    users = kernel.container.resolve("engine.users", UserEngine); user = users.find_by_email("tool@example.test") or users.create(email="tool@example.test", display_name="Tool", role="tool-user")
    auth = kernel.container.resolve("engine.authentication", AuthenticationEngine); auth.set_password(user.user_id, "correct horse battery staple")
    login = auth.login(email="tool@example.test", password="correct horse battery staple"); assert login.token is not None
    return kernel, auth.resolve(login.token.reveal())


def test_tool_contract_delegates_to_fixed_worker_and_persists_safe_job_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kernel, authentication = _kernel(tmp_path, monkeypatch)
    try:
        tools = kernel.container.resolve("engine.tools", ToolEngine); worker = Worker(); tools.register_provider("default", worker)
        plugin = tools.for_plugin(OWNER); plugin.register(_contract()); media_id = "12345678-1234-1234-1234-123456789012"
        submitted = plugin.submit("favorite.tool.ocr", {"media_id": media_id, "language": "ben"}, authentication)
        assert submitted.status is ToolJobStatus.RUNNING and worker.inputs == [{"media_id": media_id, "language": "ben"}]
        external = f"worker:{submitted.job_id}"; worker.jobs[external] = ToolWorkerState(ToolJobStatus.COMPLETED, 100, {"text_media_id": media_id})
        completed = plugin.status("favorite.tool.ocr", submitted.job_id, authentication)
        assert completed.status is ToolJobStatus.COMPLETED and completed.result == {"text_media_id": media_id}
        plugin.unregister_all(); assert tools.contracts(OWNER) == ()
    finally: kernel.shutdown()


def test_tool_input_is_bounded_and_worker_destination_is_not_plugin_controlled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kernel, authentication = _kernel(tmp_path, monkeypatch)
    try:
        tools = kernel.container.resolve("engine.tools", ToolEngine); plugin = tools.for_plugin(OWNER); plugin.register(_contract())
        assert plugin.availability("favorite.tool.ocr") == "not_configured"
        with pytest.raises(ToolError): plugin.submit("favorite.tool.ocr", {"media_id": "12345678-1234-1234-1234-123456789012", "language": "eng"}, authentication)
        with pytest.raises(InvalidTool): plugin.submit("favorite.tool.ocr", {"media_id": "../../secret", "language": "eng"}, authentication)
        with pytest.raises(InvalidTool): tools.for_plugin("favorite.plugin.other").register(_contract())
    finally: kernel.shutdown()
