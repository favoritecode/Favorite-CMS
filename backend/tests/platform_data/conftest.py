from collections.abc import Iterator
from pathlib import Path

import pytest

from backend.bootstrap import build_kernel
from backend.core import Kernel
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.authentication import AuthenticationContext, AuthenticationEngine
from backend.engines.permissions import PermissionDefinition, PermissionEngine
from backend.engines.users import UserEngine


@pytest.fixture
def data_kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Kernel]:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'phase5.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-five-test-signing-key-at-least-thirty-two-bytes")
    kernel = build_kernel(); kernel.bootstrap()
    migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history()
    applied = migrations.upgrade()
    assert set(applied) == {
        "platform.user.001", "platform.authentication.001", "platform.content.001",
            "platform.media.001", "platform.settings.001", "platform.menu.001", "platform.seo.001",
        "platform.update.001",
        "platform.installation.001",
        "platform.permission.001",
    }
    assert migrations.upgrade() == ()
    yield kernel
    kernel.shutdown()


def authenticated(kernel: Kernel, *, email: str = "owner@example.com", role: str = "member") -> AuthenticationContext:
    users = kernel.container.resolve("engine.users", UserEngine)
    authentication = kernel.container.resolve("engine.authentication", AuthenticationEngine)
    user = users.find_by_email(email)
    if user is None:
        user = users.create(email=email, display_name="Owner", role=role)
        authentication.set_password(user.user_id, "correct horse battery staple")
    result = authentication.login(email=email, password="correct horse battery staple")
    assert result.success
    return result.context


def permission(kernel: Kernel, permission_id: str, action: str, resource_type: str,
               *, allow_owner: bool = False, allow_public: bool = False) -> None:
    kernel.container.resolve("engine.permissions", PermissionEngine).register(
        PermissionDefinition(permission_id, "tests", action, resource_type, allow_owner, allow_public)
    )
