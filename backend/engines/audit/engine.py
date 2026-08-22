"""Secret-free administration audit ownership."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, MetaData, String, Table, insert, select

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration


@dataclass(frozen=True)
class AuditRecord:
    record_id: str
    actor_user_id: str
    action: str
    target_type: str
    target_id: str
    created_at: str


_metadata = MetaData()
_records = Table("favorite_audit_records", _metadata,
    Column("record_id", String(36), primary_key=True), Column("actor_user_id", String(36), nullable=False),
    Column("action", String(128), nullable=False), Column("target_type", String(64), nullable=False),
    Column("target_id", String(255), nullable=False), Column("created_at", String(64), nullable=False))


def audit_migration() -> Migration:
    return Migration("platform.audit.001", "engine.audit", lambda connection: _metadata.create_all(connection, tables=[_records]))


class AuditEngine:
    engine_id = "audit"
    dependencies = ("database", "migrations")

    def __init__(self) -> None:
        self._database: DatabaseEngine | None = None
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(audit_migration())
        container.register("engine.audit", self)

    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False

    def record(self, *, actor_user_id: str, action: str, target_type: str, target_id: str) -> AuditRecord:
        values = AuditRecord(str(uuid4()), actor_user_id, _bounded(action, 128), _bounded(target_type, 64), _bounded(target_id, 255), datetime.now(timezone.utc).isoformat())
        with self._database_required().transaction() as session:
            session.execute(insert(_records).values(**values.__dict__))
        return values

    def recent(self, *, limit: int = 100) -> tuple[AuditRecord, ...]:
        bounded = max(1, min(limit, 100))
        with self._database_required().session() as session:
            rows = session.execute(select(_records).order_by(_records.c.created_at.desc()).limit(bounded)).mappings().all()
        return tuple(AuditRecord(**dict(row)) for row in rows)

    def _database_required(self) -> DatabaseEngine:
        if self._database is None or not self.ready: raise RuntimeError("Audit persistence is unavailable")
        return self._database


def _bounded(value: str, maximum: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > maximum: raise ValueError("Audit metadata is invalid")
    return normalized
