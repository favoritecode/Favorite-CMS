"""Explicit, ordered SQLAlchemy migration coordination."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from sqlalchemy import Column, MetaData, String, Table, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Connection

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine


class MigrationError(RuntimeError):
    pass


Upgrade = Callable[[Connection], None]


@dataclass(frozen=True)
class Migration:
    migration_id: str
    owner: str
    upgrade: Upgrade
    dependencies: tuple[str, ...] = ()
    providers: frozenset[str] = frozenset({"sqlite", "postgresql"})
    reversible: bool = False

    def __post_init__(self) -> None:
        if not self.migration_id.strip() or not self.owner.strip():
            raise MigrationError("Migration identity and owner are required")


_metadata = MetaData()
_history = Table(
    "favorite_migration_history",
    _metadata,
    Column("migration_id", String(255), primary_key=True),
    Column("owner", String(255), nullable=False),
    Column("applied_at", String(64), nullable=False),
)
_migration_lock = Table(
    "favorite_migration_lock",
    _metadata,
    Column("lock_id", String(64), primary_key=True),
    Column("acquired_at", String(64), nullable=False),
)


class DatabaseMigrationEngine:
    engine_id = "migrations"
    dependencies = ("database",)

    def __init__(self) -> None:
        self._database: DatabaseEngine | None = None
        self._migrations: dict[str, Migration] = {}
        self._lock = Lock()
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        container.register("engine.migrations", self)

    def start(self) -> None:
        database = self._require_database()
        if not database.healthcheck():
            raise MigrationError("Migration database is unavailable")
        self.ready = True

    def shutdown(self) -> None:
        self.ready = False

    def register(self, migration: Migration) -> None:
        if migration.migration_id in self._migrations:
            raise MigrationError(f"Migration is already registered: {migration.migration_id}")
        self._migrations[migration.migration_id] = migration

    def contains(self, migration_id: str) -> bool:
        return migration_id in self._migrations

    def initialize_history(self) -> None:
        """Explicitly create migration infrastructure; never called by app startup."""
        _metadata.create_all(
            self._require_database().connection_engine(), tables=[_history, _migration_lock]
        )

    def applied(self) -> tuple[str, ...]:
        with self._require_database().connection_engine().connect() as connection:
            try:
                return tuple(connection.execute(select(_history.c.migration_id)).scalars())
            except Exception as exc:
                raise MigrationError("Migration history is unavailable") from exc

    def pending(self) -> tuple[Migration, ...]:
        applied = set(self.applied())
        return tuple(item for item in self._ordered() if item.migration_id not in applied)

    def upgrade(self) -> tuple[str, ...]:
        if not self._lock.acquire(blocking=False):
            raise MigrationError("Migration lock is unavailable")
        completed: list[str] = []
        database_lock_acquired = False
        try:
            database = self._require_database()
            self._acquire_database_lock(database)
            database_lock_acquired = True
            provider = database.provider
            pending = self.pending()
            for migration in pending:
                if provider not in migration.providers:
                    raise MigrationError(
                        f"Migration is incompatible with database provider: {migration.migration_id}"
                    )
                try:
                    with database.connection_engine().begin() as connection:
                        migration.upgrade(connection)
                        connection.execute(
                            insert(_history).values(
                                migration_id=migration.migration_id,
                                owner=migration.owner,
                                applied_at=datetime.now(timezone.utc).isoformat(),
                            )
                        )
                    completed.append(migration.migration_id)
                except Exception as exc:
                    raise MigrationError(f"Migration failed: {migration.migration_id}") from exc
            return tuple(completed)
        finally:
            if database_lock_acquired and self._database is not None:
                self._release_database_lock(self._database)
            self._lock.release()

    def _ordered(self) -> tuple[Migration, ...]:
        visiting: set[str] = set()
        visited: set[str] = set()
        result: list[Migration] = []

        def visit(identifier: str) -> None:
            if identifier in visiting:
                raise MigrationError("Circular migration dependency detected")
            if identifier in visited:
                return
            migration = self._migrations[identifier]
            visiting.add(identifier)
            for dependency in sorted(migration.dependencies):
                if dependency not in self._migrations:
                    raise MigrationError(f"Migration dependency is unresolved: {dependency}")
                visit(dependency)
            visiting.remove(identifier)
            visited.add(identifier)
            result.append(migration)

        for identifier in sorted(self._migrations):
            visit(identifier)
        return tuple(result)

    def _require_database(self) -> DatabaseEngine:
        if self._database is None:
            raise MigrationError("Migration Engine is not initialized")
        return self._database

    def _acquire_database_lock(self, database: DatabaseEngine) -> None:
        try:
            with database.connection_engine().begin() as connection:
                connection.execute(
                    insert(_migration_lock).values(
                        lock_id="migration-sequence",
                        acquired_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
        except IntegrityError as exc:
            raise MigrationError("Migration lock is unavailable") from exc
        except Exception as exc:
            raise MigrationError("Migration lock could not be acquired") from exc

    def _release_database_lock(self, database: DatabaseEngine) -> None:
        try:
            with database.connection_engine().begin() as connection:
                connection.execute(
                    delete(_migration_lock).where(_migration_lock.c.lock_id == "migration-sequence")
                )
        except Exception:
            # Do not replace the primary migration result with lock cleanup failure.
            pass
