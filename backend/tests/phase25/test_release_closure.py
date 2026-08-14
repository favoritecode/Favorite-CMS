from __future__ import annotations

import io
from pathlib import Path

from backend.bootstrap import build_kernel
from backend.cli import main
from backend.engines.authentication import AuthenticationEngine
from backend.engines.permissions import AuthorizationContext, PermissionEngine
from backend.engines.users import UserEngine


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


def test_explicit_post_install_role_grant_is_owner_validated_and_persisted(tmp_path: Path, monkeypatch) -> None:
    _environment(tmp_path, monkeypatch)
    assert main(["migrate"]) == 0
    authorization = "admin.content.manage:application.admin.platform:manage:admin_content"
    assert main(["grant-role", "--role", "content-operator", "--authorization", authorization]) == 0
    assert main(["grant-role", "--role", "content-operator", "--authorization", authorization]) == 0
    assert main(["grant-role", "--role", "content-operator", "--authorization",
                 "platform.content.create:wrong.owner:create:content"]) == 1

    kernel = build_kernel()
    try:
        kernel.bootstrap()
        users = kernel.container.resolve("engine.users", UserEngine)
        authentication = kernel.container.resolve("engine.authentication", AuthenticationEngine)
        user = users.create(email="content-operator@example.invalid", display_name="Content Operator",
                            role="content-operator")
        authentication.set_password(user.user_id, "a secure content operator password")
        login = authentication.login(email="content-operator@example.invalid",
                                     password="a secure content operator password")
        decision = kernel.container.resolve("engine.permissions", PermissionEngine).evaluate(
            "admin.content.manage", AuthorizationContext("manage", "admin_content", login.context))
        assert decision.allowed and decision.reason == "role_grant"
    finally:
        kernel.shutdown()
