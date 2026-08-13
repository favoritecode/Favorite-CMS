"""Verified, provider-neutral Backup Set coordination."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
from threading import Lock
from uuid import uuid4

from backend.core.container import ServiceContainer
from backend.core.extensions import ExtensionManager, ExtensionState
from backend.database import DatabaseEngine
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.storage import StorageEngine, StorageReference, StorageScope

class BackupFailure(ApplicationFailure): pass
class InvalidBackup(ValidationFailure): pass

@dataclass(frozen=True)
class BackupScope:
    storage_scopes: tuple[StorageScope, ...] = ()

@dataclass(frozen=True)
class BackupMetadata:
    backup_id: str
    created_at: str
    platform_version: str
    database_provider: str
    storage_scope_keys: tuple[str, ...]
    checksum: str
    verified: bool
    reference: StorageReference

class BackupRecoveryEngine:
    engine_id = "recovery"
    dependencies = ("database", "storage", "migrations", "plugins", "themes")
    _destination = StorageScope("sets", "platform.backup")
    def __init__(self, platform_version: str = "0.1.0") -> None:
        self._database: DatabaseEngine | None = None; self._storage: StorageEngine | None = None
        self._extensions: ExtensionManager | None = None; self._platform_version = platform_version
        self._records: dict[str, BackupMetadata] = {}; self._lock = Lock(); self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine); self._storage = container.resolve("engine.storage", StorageEngine)
        self._extensions = container.resolve("core.extensions", ExtensionManager)
        container.register("engine.recovery", self)
    def start(self) -> None:
        self.ready = True
        self.discover()
    def shutdown(self) -> None: self.ready = False
    def create(self, scope: BackupScope) -> BackupMetadata:
        if not self._lock.acquire(blocking=False): raise BackupFailure("Backup operation is already active")
        try:
            database = self._database_required().export_snapshot()
            objects: dict[str, dict[str, str]] = {}
            for storage_scope in sorted(scope.storage_scopes, key=lambda item: item.key):
                values: dict[str, str] = {}
                for reference in self._storage_required().list(storage_scope):
                    values[reference.identifier] = base64.b64encode(self._storage_required().retrieve(reference, scope=storage_scope)).decode("ascii")
                objects[storage_scope.key] = values
            extensions = {identifier: {"version": self._extensions_required().manifest(identifier).version,
                                        "state": self._extensions_required().state(identifier).value}
                          for identifier in self._extensions_required().registered()}
            backup_id = str(uuid4()); created_at = datetime.now(timezone.utc).isoformat()
            payload = {"format": 1, "backup_id": backup_id, "created_at": created_at, "platform_version": self._platform_version,
                       "database_provider": self._database_required().provider,
                       "database": base64.b64encode(database).decode("ascii"), "storage": objects, "extensions": extensions}
            canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            checksum = hashlib.sha256(canonical).hexdigest(); envelope = json.dumps({"checksum": checksum, "payload": payload}, sort_keys=True, separators=(",", ":")).encode()
            reference = self._storage_required().store(self._destination, f"{backup_id}.json", envelope)
            verified = self._verify_bytes(envelope)
            metadata = BackupMetadata(backup_id, created_at, self._platform_version,
                                      self._database_required().provider, tuple(sorted(objects)), checksum, verified, reference)
            if not verified:
                self._storage_required().delete(reference, scope=self._destination)
                raise BackupFailure("Backup verification failed")
            self._records[backup_id] = metadata
            return metadata
        finally: self._lock.release()
    def verify(self, backup_id: str) -> bool:
        metadata = self._metadata(backup_id)
        try: return self._verify_bytes(self._storage_required().retrieve(metadata.reference, scope=self._destination))
        except Exception: return False

    def discover(self) -> tuple[BackupMetadata, ...]:
        """Rebuild the catalogue from self-describing Backup Sets after restart."""
        for reference in self._storage_required().list(self._destination):
            try:
                raw = self._storage_required().retrieve(reference, scope=self._destination)
                payload = self._validated_payload(raw)
                backup_id = str(payload["backup_id"])
                storage = payload.get("storage")
                if not isinstance(storage, dict): continue
                self._records[backup_id] = BackupMetadata(
                    backup_id, str(payload["created_at"]), str(payload["platform_version"]),
                    str(payload["database_provider"]), tuple(sorted(storage)),
                    hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                    self._verify_bytes(raw), reference,
                )
            except Exception:
                continue
        return tuple(self._records[key] for key in sorted(self._records))
    def restore(self, backup_id: str, *, expected_platform_version: str) -> None:
        if not self._lock.acquire(blocking=False): raise BackupFailure("Recovery operation is already active")
        try:
            metadata = self._metadata(backup_id); raw = self._storage_required().retrieve(metadata.reference, scope=self._destination)
            payload = self._validated_payload(raw)
            if expected_platform_version != self._platform_version or payload["platform_version"] != self._platform_version:
                raise InvalidBackup("Backup platform version is incompatible")
            if payload["database_provider"] != self._database_required().provider: raise InvalidBackup("Backup database provider is incompatible")
            database = base64.b64decode(payload["database"], validate=True)
            if not self._database_required().validate_snapshot(database): raise InvalidBackup("Backup database snapshot is invalid")
            storage_payload = payload.get("storage")
            if not isinstance(storage_payload, dict): raise InvalidBackup("Backup Storage state is invalid")
            decoded: dict[StorageScope, dict[str, bytes]] = {}
            for scope_key, objects in storage_payload.items():
                owner, separator, name = str(scope_key).partition("/")
                if not separator or not isinstance(objects, dict): raise InvalidBackup("Backup Storage scope is invalid")
                storage_scope = StorageScope(name, owner); decoded[storage_scope] = {}
                for identifier, encoded in objects.items():
                    decoded[storage_scope][str(identifier)] = base64.b64decode(encoded, validate=True)
            self._validate_extensions(payload.get("extensions"))
            previous_database = self._database_required().export_snapshot()
            previous_storage = {scope: {ref.identifier: self._storage_required().retrieve(ref, scope=scope)
                                        for ref in self._storage_required().list(scope)} for scope in decoded}
            try:
                self._database_required().restore_snapshot(database)
                for storage_scope, objects in decoded.items():
                    self._replace_scope(storage_scope, objects)
                self._restore_extensions(payload.get("extensions"))
                if not self._database_required().healthcheck(): raise BackupFailure("Restored database validation failed")
            except Exception:
                self._database_required().restore_snapshot(previous_database)
                for storage_scope, objects in previous_storage.items():
                    self._replace_scope(storage_scope, objects)
                raise
        except (InvalidBackup, BackupFailure): raise
        except Exception as exc: raise BackupFailure("Backup restore failed") from exc
        finally: self._lock.release()
    def metadata(self, backup_id: str) -> BackupMetadata: return self._metadata(backup_id)
    def operational_status(self) -> dict[str, object]:
        """Expose recovery readiness without backup paths or snapshot contents."""
        return {"status": "healthy" if self.ready else "unavailable", "backup_count": len(self._records),
                "mode": "explicit", "native_postgresql_restore": False}
    def _verify_bytes(self, raw: bytes) -> bool:
        try:
            payload = self._validated_payload(raw); database = base64.b64decode(payload["database"], validate=True)
            return self._database_required().validate_snapshot(database)
        except Exception: return False
    def _validated_payload(self, raw: bytes) -> dict[str, object]:
        try: envelope = json.loads(raw)
        except (TypeError, ValueError, UnicodeDecodeError) as exc: raise InvalidBackup("Backup format is invalid") from exc
        if not isinstance(envelope, dict): raise InvalidBackup("Backup format is invalid")
        payload = envelope.get("payload")
        if not isinstance(payload, dict) or payload.get("format") != 1: raise InvalidBackup("Backup format is invalid")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        if not isinstance(envelope.get("checksum"), str) or not hmac.compare_digest(envelope["checksum"], hashlib.sha256(canonical).hexdigest()):
            raise InvalidBackup("Backup integrity validation failed")
        return payload
    def _restore_extensions(self, value: object) -> None:
        self._validate_extensions(value)
        assert isinstance(value, dict)
        for identifier, snapshot in value.items():
            assert isinstance(snapshot, dict)
            target = snapshot.get("state")
            if target == ExtensionState.ENABLED.value and self._extensions_required().state(identifier) is not ExtensionState.ENABLED:
                if not self._extensions_required().enable(identifier): raise BackupFailure("Extension recovery failed")
            elif target == ExtensionState.DISABLED.value and self._extensions_required().state(identifier) is ExtensionState.ENABLED:
                if not self._extensions_required().disable(identifier): raise BackupFailure("Extension recovery failed")

    def _validate_extensions(self, value: object) -> None:
        if not isinstance(value, dict): raise InvalidBackup("Backup Extension state is invalid")
        for identifier, snapshot in value.items():
            if identifier not in self._extensions_required().registered() or not isinstance(snapshot, dict): raise InvalidBackup("Backup Extension is unavailable")
            if self._extensions_required().manifest(identifier).version != snapshot.get("version"): raise InvalidBackup("Backup Extension version is incompatible")
            if snapshot.get("state") not in {state.value for state in ExtensionState}: raise InvalidBackup("Backup Extension state is invalid")
    def _metadata(self, backup_id: str) -> BackupMetadata:
        try: return self._records[backup_id]
        except KeyError as exc: raise InvalidBackup("Backup Set is unavailable") from exc
    def _replace_scope(self, scope: StorageScope, objects: dict[str, bytes]) -> None:
        for reference in self._storage_required().list(scope):
            if reference.identifier not in objects:
                self._storage_required().delete(reference, scope=scope)
        for identifier, value in objects.items():
            self._storage_required().store(scope, identifier, value, overwrite=True)
    def _database_required(self) -> DatabaseEngine:
        if self._database is None: raise BackupFailure("Database backup boundary is unavailable")
        return self._database
    def _storage_required(self) -> StorageEngine:
        if self._storage is None: raise BackupFailure("Backup Storage boundary is unavailable")
        return self._storage
    def _extensions_required(self) -> ExtensionManager:
        if self._extensions is None: raise BackupFailure("Extension recovery boundary is unavailable")
        return self._extensions
