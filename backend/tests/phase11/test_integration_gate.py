"""Document 040/044 regression gates not owned by a single Engine suite."""
from dataclasses import dataclass
import inspect
from pathlib import Path

from sqlalchemy import inspect as sqlalchemy_inspect

from backend.bootstrap import build_kernel
from backend.core.extensions import ExtensionManager, ExtensionManifest, ExtensionState
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.api import APIEngine
from backend.engines.media import MediaEngine
from backend.engines.plugins import PluginContext, PluginEngine
from backend.engines.rendering import RenderingEngine
from backend.engines.routing import RoutingEngine
from backend.recovery import BackupRecoveryEngine, BackupScope
from backend.tests.extensions.conftest import manifest_data


@dataclass
class Runtime:
    def register(self, context: PluginContext) -> None: pass
    def activate(self) -> None: pass
    def deactivate(self) -> None: pass
    def unregister(self) -> None: pass


def configured_kernel(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'phase11.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-eleven-signing-key-at-least-thirty-two-bytes")
    kernel = build_kernel(); kernel.bootstrap(); return kernel


def test_normal_startup_does_not_create_or_migrate_schema(tmp_path: Path, monkeypatch) -> None:
    kernel = configured_kernel(tmp_path, monkeypatch)
    try:
        database = kernel.container.resolve("engine.database", DatabaseEngine)
        assert sqlalchemy_inspect(database.connection_engine()).get_table_names() == []
    finally: kernel.shutdown()


def test_document_044_corrected_ownership_has_regression_guards() -> None:
    api_source = inspect.getsource(APIEngine)
    rendering_source = inspect.getsource(RenderingEngine)
    media_source = inspect.getsource(MediaEngine)
    routing_source = inspect.getsource(RoutingEngine)
    assert "self._routes" in routing_source
    assert "self._routes" not in api_source
    assert "def resolve(" not in rendering_source and "self._routes" not in rendering_source
    assert "StorageProvider" not in media_source and "LocalStorageProvider" not in media_source


def test_backup_restore_recovers_compatible_extension_state(tmp_path: Path, monkeypatch) -> None:
    kernel = configured_kernel(tmp_path, monkeypatch)
    try:
        migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
        migrations.initialize_history(); migrations.upgrade()
        manager = kernel.container.resolve("core.extensions", ExtensionManager)
        manifest = ExtensionManifest.from_mapping(manifest_data(id="favorite.plugin.recovery"))
        manager.register(manifest)
        plugins = kernel.container.resolve("engine.plugins", PluginEngine)
        plugins.bind(manifest.id, Runtime()); assert plugins.activate(manifest.id)
        recovery = kernel.container.resolve("engine.recovery", BackupRecoveryEngine)
        backup = recovery.create(BackupScope())
        assert plugins.deactivate(manifest.id)
        assert manager.state(manifest.id) is ExtensionState.DISABLED
        recovery.restore(backup.backup_id, expected_platform_version="0.1.0")
        assert manager.state(manifest.id) is ExtensionState.ENABLED
    finally: kernel.shutdown()
