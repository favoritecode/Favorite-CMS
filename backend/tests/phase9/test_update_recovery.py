from dataclasses import dataclass
import hashlib
from pathlib import Path
from threading import Event, Thread

import pytest
from sqlalchemy import text

from backend.bootstrap import build_kernel
from backend.core.extensions import ExtensionManager, ExtensionManifest, ExtensionState, ExtensionType
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.plugins import PluginContext, PluginEngine
from backend.engines.storage import StorageEngine, StorageScope
from backend.engines.themes import ThemeEngine, ThemePackage
from backend.recovery import BackupRecoveryEngine, BackupScope, InvalidBackup
from backend.tests.extensions.conftest import manifest_data
from backend.update import InvalidUpdate, UpdateCandidate, UpdateEngine, UpdatePackage, UpdateState


@dataclass
class Runtime:
    fail: bool = False
    entered: Event | None = None
    release: Event | None = None
    def register(self, context: PluginContext) -> None: pass
    def activate(self) -> None:
        if self.entered: self.entered.set()
        if self.release: self.release.wait(2)
        if self.fail: raise RuntimeError("activation failed")
    def deactivate(self) -> None: pass
    def unregister(self) -> None: pass


def manifest(version: str = "1.0.0", **overrides: object) -> ExtensionManifest:
    return ExtensionManifest.from_mapping(manifest_data(id="favorite.plugin.phase9", version=version, **overrides))


@pytest.fixture
def kernel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FAVORITE_ENV", "test")
    monkeypatch.setenv("FAVORITE_DATABASE_URL", f"sqlite+pysqlite:///{tmp_path / 'phase9.db'}")
    monkeypatch.setenv("FAVORITE_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("FAVORITE_AUTH_JWT_SECRET", "phase-nine-test-signing-key-at-least-thirty-two-bytes")
    value = build_kernel(); value.bootstrap()
    migrations = value.container.resolve("engine.migrations", DatabaseMigrationEngine)
    migrations.initialize_history(); migrations.upgrade()
    yield value
    value.shutdown()


def installed(kernel, *, active: bool = True):
    manager = kernel.container.resolve("core.extensions", ExtensionManager)
    plugins = kernel.container.resolve("engine.plugins", PluginEngine)
    manager.register(manifest()); plugins.bind("favorite.plugin.phase9", Runtime())
    if active: assert plugins.activate("favorite.plugin.phase9")
    return manager, plugins


def candidate(version: str = "1.1.0", *, runtime: Runtime | None = None, artifact: bytes = b"package", **kwargs):
    package = UpdatePackage("phase9-package", "favorite.plugin.phase9", ExtensionType.PLUGIN,
                            manifest(version), artifact, hashlib.sha256(artifact).hexdigest(), **kwargs)
    return UpdateCandidate(package, runtime or Runtime())


def test_valid_update_is_staged_verified_recorded_and_repeat_rejected(kernel) -> None:
    manager, _ = installed(kernel); updates = kernel.container.resolve("engine.update", UpdateEngine)
    result = updates.apply(candidate())
    assert result.state is UpdateState.COMPLETED and result.final_version == "1.1.0"
    assert manager.state("favorite.plugin.phase9") is ExtensionState.ENABLED
    assert kernel.container.resolve("engine.storage", StorageEngine).list(StorageScope("staging", "platform.update")) == ()
    repeated = updates.apply(candidate())
    assert repeated.state is UpdateState.ROLLED_BACK


def test_update_validation_dependency_and_activation_fail_closed(kernel) -> None:
    manager, _ = installed(kernel); updates = kernel.container.resolve("engine.update", UpdateEngine)
    bad = candidate(); bad = UpdateCandidate(UpdatePackage(
        bad.package.package_id, bad.package.target_id, bad.package.target_type, bad.package.manifest,
        bad.package.artifact, "0" * 64), Runtime())
    assert updates.apply(bad).state is UpdateState.ROLLED_BACK
    assert updates.apply(candidate("1.1.0", runtime=Runtime(fail=True))).state is UpdateState.ROLLED_BACK
    assert manager.manifest("favorite.plugin.phase9").version == "1.0.0"
    incompatible = candidate("1.1.0")
    incompatible_manifest = manifest("1.1.0", minimumCoreVersion="9.0.0", maximumCoreVersion="10.0.0")
    incompatible = UpdateCandidate(UpdatePackage("x", incompatible.package.target_id, ExtensionType.PLUGIN,
        incompatible_manifest, b"x", hashlib.sha256(b"x").hexdigest()), Runtime())
    assert updates.apply(incompatible).state is UpdateState.ROLLED_BACK


def test_migration_coordination_and_failure_state(kernel) -> None:
    manager, _ = installed(kernel); updates = kernel.container.resolve("engine.update", UpdateEngine)
    migration = Migration("favorite.plugin.phase9.001", "favorite.plugin.phase9",
                          lambda connection: connection.execute(text("CREATE TABLE phase9_data (id INTEGER)")))
    result = updates.apply(candidate(migrations=(migration,)))
    assert result.state is UpdateState.COMPLETED and result.migration_status == "completed"
    assert "favorite.plugin.phase9.001" in kernel.container.resolve("engine.migrations", DatabaseMigrationEngine).applied()
    assert manager.manifest("favorite.plugin.phase9").version == "1.1.0"


def test_target_lock_rejects_concurrent_update(kernel) -> None:
    installed(kernel); updates = kernel.container.resolve("engine.update", UpdateEngine)
    entered, release = Event(), Event(); results = []
    thread = Thread(target=lambda: results.append(updates.apply(candidate(runtime=Runtime(entered=entered, release=release)))) )
    thread.start(); assert entered.wait(2)
    with pytest.raises(Exception, match="already being updated"): updates.apply(candidate("1.2.0"))
    release.set(); thread.join(3)
    assert results[0].state is UpdateState.COMPLETED


def test_verified_backup_restore_and_restart_discovery(kernel) -> None:
    database = kernel.container.resolve("engine.database", DatabaseEngine)
    storage = kernel.container.resolve("engine.storage", StorageEngine); scope = StorageScope("files", "phase9")
    reference = storage.store(scope, "item.txt", b"before")
    with database.transaction() as session: session.execute(text("CREATE TABLE recovery_probe (value TEXT)")); session.execute(text("INSERT INTO recovery_probe VALUES ('before')"))
    recovery = kernel.container.resolve("engine.recovery", BackupRecoveryEngine)
    backup = recovery.create(BackupScope((scope,))); assert backup.verified and recovery.verify(backup.backup_id)
    storage.store(scope, "item.txt", b"after", overwrite=True)
    storage.store(scope, "extra.txt", b"not-in-backup")
    with database.transaction() as session: session.execute(text("UPDATE recovery_probe SET value='after'"))
    recovery.restore(backup.backup_id, expected_platform_version="0.1.0")
    assert storage.retrieve(reference, scope=scope) == b"before"
    assert tuple(item.identifier for item in storage.list(scope)) == ("item.txt",)
    with database.session() as session: assert session.execute(text("SELECT value FROM recovery_probe")).scalar_one() == "before"
    recovery._records.clear()
    assert any(item.backup_id == backup.backup_id for item in recovery.discover())


def test_backup_integrity_and_compatibility_fail_closed(kernel) -> None:
    recovery = kernel.container.resolve("engine.recovery", BackupRecoveryEngine)
    backup = recovery.create(BackupScope())
    with pytest.raises(InvalidBackup, match="incompatible"):
        recovery.restore(backup.backup_id, expected_platform_version="9.0.0")
    storage = kernel.container.resolve("engine.storage", StorageEngine)
    storage.store(backup.reference.scope, backup.reference.identifier, b"tampered", overwrite=True)
    assert not recovery.verify(backup.backup_id)
    with pytest.raises(InvalidBackup): recovery.restore(backup.backup_id, expected_platform_version="0.1.0")


def test_theme_update_uses_theme_validation_and_rolls_back(kernel, tmp_path: Path) -> None:
    manager = kernel.container.resolve("core.extensions", ExtensionManager)
    themes = kernel.container.resolve("engine.themes", ThemeEngine)
    raw = manifest_data(id="favorite.theme.phase9", type="theme")
    old_manifest = ExtensionManifest.from_mapping(raw); manager.register(old_manifest)
    old_root = tmp_path / "old"; old_root.mkdir(); (old_root / "page.html").write_text("old", encoding="utf-8")
    old_package = ThemePackage(old_root, templates=("page.html",)); themes.bind(old_manifest.id, old_package, Runtime())
    assert themes.activate(old_manifest.id)
    new_manifest = ExtensionManifest.from_mapping({**raw, "version": "1.1.0"})
    invalid = ThemePackage(old_root, templates=("missing.html",))
    package = UpdatePackage("theme-package", old_manifest.id, ExtensionType.THEME, new_manifest,
                            b"theme", hashlib.sha256(b"theme").hexdigest())
    result = kernel.container.resolve("engine.update", UpdateEngine).apply(UpdateCandidate(package, Runtime(), invalid))
    assert result.state is UpdateState.ROLLED_BACK
    assert themes.manifest(old_manifest.id).version == "1.0.0" and themes.package(old_manifest.id) is old_package
