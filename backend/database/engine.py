"""SQLAlchemy connection, session, and transaction infrastructure."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import sqlite3
import tempfile
from pathlib import Path

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import Configuration, SecretValue
from backend.core.container import ServiceContainer


class DatabaseUnavailable(RuntimeError):
    """Controlled database infrastructure failure without provider details."""

class DatabaseSnapshotError(DatabaseUnavailable): pass


class DatabaseEngine:
    engine_id = "database"
    dependencies: tuple[str, ...] = ()

    def __init__(self) -> None:
        self._engine: Engine | None = None
        self._sessions: sessionmaker[Session] | None = None
        self._configuration: Configuration | None = None

    @property
    def provider(self) -> str:
        engine = self._require_engine()
        return engine.url.get_backend_name()

    @property
    def ready(self) -> bool:
        return self._engine is not None and self._sessions is not None

    def initialize(self, container: ServiceContainer) -> None:
        self._configuration = container.resolve("core.configuration", Configuration)
        container.register("engine.database", self)

    def start(self) -> None:
        if self._configuration is None:
            raise DatabaseUnavailable("Database configuration is unavailable")
        secret_url = self._configuration.get("database.url", SecretValue)
        url = make_url(secret_url.reveal())
        if url.get_backend_name() not in {"sqlite", "postgresql"}:
            raise DatabaseUnavailable("Database provider is unsupported")
        kwargs: dict[str, object] = {"pool_pre_ping": True}
        if url.get_backend_name() == "sqlite":
            kwargs["connect_args"] = {"check_same_thread": False}
            if url.database in {None, "", ":memory:"}:
                kwargs["poolclass"] = StaticPool
        try:
            engine = create_engine(url, **kwargs)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            self._engine = engine
            self._sessions = sessionmaker(bind=engine, expire_on_commit=False)
        except Exception as exc:
            self._engine = None
            self._sessions = None
            raise DatabaseUnavailable("Database is unavailable") from exc

    def shutdown(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._sessions = None

    def healthcheck(self) -> bool:
        try:
            with self._require_engine().connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Yield an explicit session; callers own commit semantics."""
        factory = self._require_sessions()
        database_session = factory()
        try:
            yield database_session
        except SQLAlchemyError as exc:
            database_session.rollback()
            raise DatabaseUnavailable("Database operation failed") from exc
        except Exception:
            database_session.rollback()
            raise
        finally:
            database_session.close()

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        """Commit on successful owner operation and roll back on failure."""
        with self.session() as database_session:
            try:
                yield database_session
                database_session.commit()
            except SQLAlchemyError as exc:
                database_session.rollback()
                raise DatabaseUnavailable("Database transaction failed") from exc
            except Exception:
                database_session.rollback()
                raise

    def connection_engine(self) -> Engine:
        """Approved infrastructure access for the Migration Engine only."""
        return self._require_engine()

    def export_snapshot(self) -> bytes:
        """Provider-owned SQLite recovery artifact; PostgreSQL requires an injected production adapter."""
        engine = self._require_engine()
        if self.provider != "sqlite": raise DatabaseSnapshotError("Database snapshot provider is unavailable")
        source = engine.raw_connection()
        try:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle: path = Path(handle.name)
            destination = sqlite3.connect(path)
            try:
                source.driver_connection.backup(destination)  # type: ignore[attr-defined]
                destination.execute("PRAGMA integrity_check").fetchone()
            finally: destination.close()
            return path.read_bytes()
        except Exception as exc: raise DatabaseSnapshotError("Database snapshot creation failed") from exc
        finally:
            source.close()
            if 'path' in locals(): path.unlink(missing_ok=True)

    def validate_snapshot(self, data: bytes) -> bool:
        if self.provider != "sqlite" or not isinstance(data, bytes) or not data: return False
        try:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle: path = Path(handle.name); handle.write(data)
            connection = sqlite3.connect(path)
            try: return connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            finally: connection.close()
        except Exception: return False
        finally:
            if 'path' in locals(): path.unlink(missing_ok=True)

    def restore_snapshot(self, data: bytes) -> None:
        if not self.validate_snapshot(data): raise DatabaseSnapshotError("Database snapshot is invalid")
        engine = self._require_engine()
        try:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as handle: path = Path(handle.name); handle.write(data)
            source = sqlite3.connect(path); target = engine.raw_connection()
            try: source.backup(target.driver_connection)  # type: ignore[attr-defined]
            finally: target.close(); source.close()
        except Exception as exc: raise DatabaseSnapshotError("Database snapshot restore failed") from exc
        finally:
            if 'path' in locals(): path.unlink(missing_ok=True)

    def _require_engine(self) -> Engine:
        if self._engine is None:
            raise DatabaseUnavailable("Database Engine is not started")
        return self._engine

    def _require_sessions(self) -> sessionmaker[Session]:
        if self._sessions is None:
            raise DatabaseUnavailable("Database Engine is not started")
        return self._sessions
