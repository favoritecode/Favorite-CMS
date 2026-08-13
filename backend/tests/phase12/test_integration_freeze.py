"""Executable integration-freeze checks for Documents 044 and 045 section 16."""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

from backend.admin import AdminEngine, AdminPlatformEngine
from backend.bootstrap import build_kernel
from backend.core import Kernel
from backend.engines.api import APIEngine
from backend.engines.media import MediaEngine
from backend.engines.rendering import RenderingEngine
from backend.engines.routing import RoutingEngine
from backend.engines.scheduler import SchedulerEngine

ROOT = Path(__file__).parents[3]


def _python_sources(relative: str) -> tuple[Path, ...]:
    return tuple(sorted((ROOT / relative).rglob("*.py")))


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module: result.add(node.module)
    return result


def test_forbidden_cross_layer_imports_are_absent() -> None:
    admin_imports = set().union(*(_imports(path) for path in _python_sources("backend/admin")))
    theme_imports = set().union(*(_imports(path) for path in _python_sources("backend/engines/themes")))
    core_imports = set().union(*(_imports(path) for path in _python_sources("backend/core")))
    assert not any(name.startswith(("backend.database", "backend.engines.storage", "sqlalchemy")) for name in admin_imports)
    assert not any(name.startswith(("backend.database", "backend.engines.storage", "backend.engines.authentication", "backend.engines.permissions", "sqlalchemy")) for name in theme_imports)
    assert not any(name.startswith(("backend.engines.plugins", "backend.engines.themes")) for name in core_imports)


def test_corrected_ownership_has_one_implementation_boundary() -> None:
    routing = inspect.getsource(RoutingEngine)
    api = inspect.getsource(APIEngine)
    rendering = inspect.getsource(RenderingEngine)
    media = inspect.getsource(MediaEngine)
    scheduler = inspect.getsource(SchedulerEngine)
    assert "self._routes" in routing
    assert "self._routes" not in api and "def resolve(" not in api
    assert "self._routes" not in rendering and "def resolve(" not in rendering
    assert "StorageProvider" not in media and "LocalStorageProvider" not in media
    assert "def cycle(" in scheduler and "def _require_queue(" in scheduler
    assert "self._workers" not in scheduler and "def run_worker(" not in scheduler


def test_admin_contracts_remain_clients_of_public_services() -> None:
    for kind in (AdminEngine, AdminPlatformEngine):
        source = inspect.getsource(kind)
        assert "sqlalchemy" not in source.casefold()
        assert "StorageProvider" not in source
        assert "create_all" not in source
        assert "os.getenv" not in source and "os.environ" not in source


def test_composition_lifecycle_is_deterministic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'freeze.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-twelve-signing-key-at-least-thirty-two-bytes")
    first: Kernel = build_kernel(); second: Kernel = build_kernel()
    try:
        first.bootstrap(); second.bootstrap()
        first_states = tuple(identifier for identifier, _ in first.engines.states())
        second_states = tuple(identifier for identifier, _ in second.engines.states())
        assert first_states == second_states
        assert len(first_states) == len(set(first_states))
        assert first.container.resolve("engine.routing", RoutingEngine) is not first.container.resolve("engine.api", APIEngine)
    finally:
        first.shutdown(); second.shutdown()
