from collections.abc import Iterator
from pathlib import Path
import pytest
from backend.bootstrap import build_kernel
from backend.core import Kernel
from backend.database.migrations import DatabaseMigrationEngine

@pytest.fixture
def phase7_kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Kernel]:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'phase7.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-seven-test-signing-key-at-least-thirty-two-bytes")
    kernel = build_kernel(); kernel.bootstrap()
    migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade()
    yield kernel
    kernel.shutdown()
