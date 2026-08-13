from __future__ import annotations

import io
from pathlib import Path

from backend.bootstrap import build_kernel
from backend.cli import main
from backend.engines.permissions import AuthorizationContext, PermissionEngine


def _environment(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'phase25.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "mounted"))
    monkeypatch.setenv("FAVORITE_STORAGE_PROVIDER", "mounted")
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-twenty-five-signing-secret-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_ACTIVE_THEME", "favorite.theme.starter")


def _install(permission: str, action: str, resource: str) -> list[str]:
    return [
        "install", "--email", "operator@example.invalid", "--display-name", "Operator",
        "--role", "operator", "--authorization",
        f"{permission}:application.admin.platform:{action}:{resource}", "--password-stdin",
    ]


def test_repeated_installation_cannot_add_authorization(tmp_path: Path, monkeypatch) -> None:
    _environment(tmp_path, monkeypatch)
    assert main(["migrate"]) == 0
    monkeypatch.setattr("sys.stdin", io.StringIO("a secure phase twenty five password\n"))
    assert main(_install("admin.diagnostics.view", "view", "admin_diagnostics")) == 0

    # An already-installed CLI invocation is idempotent before Theme or Permission mutation.
    monkeypatch.setattr("sys.stdin", io.StringIO("unused different password\n"))
    assert main(_install("admin.media.manage", "manage", "admin_media")) == 0

    kernel = build_kernel()
    try:
        kernel.bootstrap()
        login = kernel.container.resolve("engine.authentication").login(
            email="operator@example.invalid", password="a secure phase twenty five password"
        )
        permissions = kernel.container.resolve("engine.permissions", PermissionEngine)
        assert login.success
        assert not permissions.evaluate(
            "admin.media.manage", AuthorizationContext("manage", "admin_media", login.context)
        ).allowed
    finally:
        kernel.shutdown()
