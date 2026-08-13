from collections.abc import Iterator
from pathlib import Path

import pytest

from backend.bootstrap import build_kernel
from backend.core import Kernel
from backend.database.migrations import DatabaseMigrationEngine


@pytest.fixture
def identity_kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Kernel]:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'identity.db'}")
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "test-only-signing-key-with-at-least-thirty-two-bytes")
    monkeypatch.setenv("FAVORITE_AUTH_TOKEN_LIFETIME_SECONDS", "900")
    kernel = build_kernel()
    kernel.bootstrap()
    migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history()
    applied = migrations.upgrade()
    assert "platform.user.001" in applied
    assert "platform.authentication.001" in applied
    assert migrations.upgrade() == ()
    yield kernel
    kernel.shutdown()
