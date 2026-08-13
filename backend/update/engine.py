"""Controlled update coordination without package download or code discovery."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
from threading import Lock
from uuid import uuid4

from packaging.version import Version
from sqlalchemy import Column, MetaData, String, Table, insert, select, update

from backend.core.container import ServiceContainer
from backend.core.extensions import ExtensionManifest, ExtensionType
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration, MigrationError
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.plugins import PluginEngine, PluginRuntime
from backend.engines.storage import StorageEngine, StorageScope
from backend.engines.themes import ThemeEngine, ThemePackage, ThemeRuntime

class UpdateFailure(ApplicationFailure): pass
class InvalidUpdate(ValidationFailure): pass
class UpdateState(StrEnum):
    PENDING="pending"; VALIDATING="validating"; PREPARED="prepared"; INSTALLING="installing"; ACTIVATING="activating"; COMPLETED="completed"; FAILED="failed"; ROLLING_BACK="rolling_back"; ROLLED_BACK="rolled_back"

@dataclass(frozen=True)
class UpdatePackage:
    package_id: str
    target_id: str
    target_type: ExtensionType
    manifest: ExtensionManifest
    artifact: bytes
    checksum: str
    allow_downgrade: bool = False
    allow_reinstall: bool = False
    migrations: tuple[Migration, ...] = ()
    def __post_init__(self) -> None:
        if not self.package_id.strip() or self.manifest.id != self.target_id or self.manifest.type is not self.target_type:
            raise InvalidUpdate("Update Package identity is invalid")
        if not isinstance(self.artifact, bytes) or not self.artifact: raise InvalidUpdate("Update Package artifact is invalid")
        if len(self.checksum) != 64: raise InvalidUpdate("Update Package checksum is invalid")
        if any(migration.owner != self.target_id for migration in self.migrations): raise InvalidUpdate("Update migration owner is invalid")

@dataclass(frozen=True)
class UpdateCandidate:
    package: UpdatePackage
    runtime: PluginRuntime | ThemeRuntime
    theme_package: ThemePackage | None = None
    granted_permissions: frozenset[str] = frozenset()

@dataclass(frozen=True)
class UpdateResult:
    operation_id: str
    target_id: str
    previous_version: str
    candidate_version: str
    final_version: str
    state: UpdateState
    migration_status: str
    failure: str | None = None

_metadata=MetaData()
_updates=Table("favorite_update_history",_metadata,Column("operation_id",String(36),primary_key=True),Column("target_id",String(255),nullable=False),Column("previous_version",String(64),nullable=False),Column("candidate_version",String(64),nullable=False),Column("final_version",String(64),nullable=False),Column("state",String(32),nullable=False),Column("migration_status",String(32),nullable=False),Column("failure",String(64)))
def update_migration() -> Migration: return Migration("platform.update.001","engine.update",lambda connection:_metadata.create_all(connection,tables=[_updates]))

class UpdateEngine:
    engine_id="update"; dependencies=("database","migrations","storage","plugins","themes","settings","permissions","recovery")
    _stage_scope=StorageScope("staging","platform.update")
    def __init__(self) -> None:
        self._database:DatabaseEngine|None=None; self._migrations:DatabaseMigrationEngine|None=None; self._storage:StorageEngine|None=None
        self._plugins:PluginEngine|None=None; self._themes:ThemeEngine|None=None; self._locks:dict[str,Lock]={}; self.ready=False
    def initialize(self,container:ServiceContainer)->None:
        self._database=container.resolve("engine.database",DatabaseEngine); self._migrations=container.resolve("engine.migrations",DatabaseMigrationEngine)
        self._storage=container.resolve("engine.storage",StorageEngine); self._plugins=container.resolve("engine.plugins",PluginEngine); self._themes=container.resolve("engine.themes",ThemeEngine)
        self._migrations.register(update_migration()); container.register("engine.update",self)
    def start(self)->None:self.ready=True
    def shutdown(self)->None:self.ready=False
    def apply(self,candidate:UpdateCandidate)->UpdateResult:
        package=candidate.package; lock=self._locks.setdefault(package.target_id,Lock())
        if not lock.acquire(blocking=False): raise UpdateFailure("Update Target is already being updated")
        operation_id=str(uuid4()); previous=self._current_manifest(package).version; migration_status="not_required"; staged=None
        self._record(operation_id,package,previous,UpdateState.PENDING,migration_status,None)
        try:
            self._transition(operation_id,UpdateState.VALIDATING,previous,migration_status)
            self._validate(package,previous,candidate)
            staged=self._storage_required().store(self._stage_scope,f"{operation_id}.package",package.artifact)
            self._transition(operation_id,UpdateState.PREPARED,previous,migration_status)
            if package.migrations:
                migration_status="pending"
                for migration in package.migrations:self._migrations_required().register(migration)
            self._transition(operation_id,UpdateState.INSTALLING,previous,migration_status)
            if package.migrations:
                try:self._migrations_required().upgrade();migration_status="completed"
                except MigrationError as exc:
                    migration_status="failed";self._transition(operation_id,UpdateState.FAILED,previous,migration_status,"MigrationError")
                    return self.result(operation_id)
            self._transition(operation_id,UpdateState.ACTIVATING,previous,migration_status)
            activated=self._activate(candidate)
            final=self._current_manifest(package).version
            if not activated or final!=package.manifest.version:
                state=UpdateState.FAILED if package.migrations else UpdateState.ROLLED_BACK
                if state is UpdateState.ROLLED_BACK:
                    self._transition(operation_id,UpdateState.ROLLING_BACK,final,migration_status,"ActivationFailure")
                self._transition(operation_id,state,final,migration_status,"ActivationFailure")
                return self.result(operation_id)
            self._transition(operation_id,UpdateState.COMPLETED,final,migration_status)
            return self.result(operation_id)
        except Exception as exc:
            final=self._safe_current(package,previous); state=UpdateState.FAILED if package.migrations else UpdateState.ROLLED_BACK
            if state is UpdateState.ROLLED_BACK:
                self._transition(operation_id,UpdateState.ROLLING_BACK,final,migration_status,type(exc).__name__)
            self._transition(operation_id,state,final,migration_status,type(exc).__name__)
            return self.result(operation_id)
        finally:
            if staged is not None:
                try:self._storage_required().delete(staged,scope=self._stage_scope)
                except Exception:pass
            lock.release()
    def result(self,operation_id:str)->UpdateResult:
        with self._database_required().session() as session: row=session.execute(select(_updates).where(_updates.c.operation_id==operation_id)).mappings().one()
        return UpdateResult(row["operation_id"],row["target_id"],row["previous_version"],row["candidate_version"],row["final_version"],UpdateState(row["state"]),row["migration_status"],row["failure"])
    def operational_status(self)->dict[str,object]:
        """Expose manual update readiness without package or staging internals."""
        return {"status":"healthy" if self.ready else "unavailable","mode":"explicit","remote_updates":False,
                "active_operations":sum(lock.locked() for lock in self._locks.values())}
    def _validate(self,package:UpdatePackage,previous:str,candidate:UpdateCandidate)->None:
        if hashlib.sha256(package.artifact).hexdigest()!=package.checksum: raise InvalidUpdate("Update Package integrity validation failed")
        current=Version(previous); target=Version(package.manifest.version)
        if target==current and not package.allow_reinstall: raise InvalidUpdate("Update reinstallation is not allowed")
        if target<current and not package.allow_downgrade: raise InvalidUpdate("Update downgrade is not allowed")
        if not package.manifest.supports_core("0.1.0"): raise InvalidUpdate("Update Package is incompatible")
        if package.target_type is ExtensionType.THEME:
            if candidate.theme_package is None: raise InvalidUpdate("Theme Update Package is incomplete")
            candidate.theme_package.validate()
        elif not set(package.manifest.permissions).issubset(candidate.granted_permissions): raise InvalidUpdate("Plugin permissions were not granted")
        identifiers=[migration.migration_id for migration in package.migrations]
        if len(identifiers)!=len(set(identifiers)) or any(self._migrations_required().contains(identifier) for identifier in identifiers):
            raise InvalidUpdate("Update migration identity is already registered")
    def _activate(self,candidate:UpdateCandidate)->bool:
        package=candidate.package
        if package.target_type is ExtensionType.PLUGIN:
            return self._plugins_required().update(package.target_id,package.manifest,candidate.runtime,granted_permissions=candidate.granted_permissions) # type: ignore[arg-type]
        assert candidate.theme_package is not None
        return self._themes_required().update(package.target_id,package.manifest,candidate.theme_package,candidate.runtime) # type: ignore[arg-type]
    def _current_manifest(self,package:UpdatePackage)->ExtensionManifest:
        if package.target_type is ExtensionType.PLUGIN:
            return self._plugins_required().manifest(package.target_id)
        return self._themes_required().manifest(package.target_id)
    def _safe_current(self,package:UpdatePackage,fallback:str)->str:
        try:return self._current_manifest(package).version
        except Exception:return fallback
    def _record(self,operation_id:str,package:UpdatePackage,previous:str,state:UpdateState,migration_status:str,failure:str|None)->None:
        with self._database_required().transaction() as session:session.execute(insert(_updates).values(operation_id=operation_id,target_id=package.target_id,previous_version=previous,candidate_version=package.manifest.version,final_version=previous,state=state.value,migration_status=migration_status,failure=failure))
    def _transition(self,operation_id:str,state:UpdateState,final:str,migration_status:str,failure:str|None=None)->None:
        with self._database_required().transaction() as session:session.execute(update(_updates).where(_updates.c.operation_id==operation_id).values(state=state.value,final_version=final,migration_status=migration_status,failure=failure))
    def _database_required(self)->DatabaseEngine:
        if self._database is None:raise UpdateFailure("Update Database boundary is unavailable")
        return self._database
    def _migrations_required(self)->DatabaseMigrationEngine:
        if self._migrations is None:raise UpdateFailure("Update Migration boundary is unavailable")
        return self._migrations
    def _storage_required(self)->StorageEngine:
        if self._storage is None:raise UpdateFailure("Update Storage boundary is unavailable")
        return self._storage
    def _plugins_required(self)->PluginEngine:
        if self._plugins is None:raise UpdateFailure("Plugin Update boundary is unavailable")
        return self._plugins
    def _themes_required(self)->ThemeEngine:
        if self._themes is None:raise UpdateFailure("Theme Update boundary is unavailable")
        return self._themes
