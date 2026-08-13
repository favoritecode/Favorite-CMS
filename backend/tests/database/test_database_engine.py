from pathlib import Path

import pytest
from sqlalchemy import text

from backend.database import DatabaseEngine, DatabaseUnavailable
from backend.tests.database.conftest import database_container, started_database


def test_sqlite_engine_startup_connection_and_shutdown() -> None:
    database = started_database()
    assert database.provider == "sqlite"
    assert database.healthcheck()
    database.shutdown()
    assert not database.ready
    with pytest.raises(DatabaseUnavailable):
        with database.session():
            pass


def test_session_does_not_silently_commit() -> None:
    database = started_database()
    with database.connection_engine().begin() as connection:
        connection.execute(text("CREATE TABLE sample (value INTEGER NOT NULL)"))
    with database.session() as session:
        session.execute(text("INSERT INTO sample (value) VALUES (:value)"), {"value": 1})
    with database.session() as session:
        assert session.scalar(text("SELECT count(*) FROM sample")) == 0


def test_transaction_commits_successful_operation() -> None:
    database = started_database()
    with database.connection_engine().begin() as connection:
        connection.execute(text("CREATE TABLE sample (value INTEGER NOT NULL)"))
    with database.transaction() as session:
        session.execute(text("INSERT INTO sample (value) VALUES (:value)"), {"value": 2})
    with database.session() as session:
        assert session.scalar(text("SELECT value FROM sample")) == 2


def test_transaction_rolls_back_failed_operation() -> None:
    database = started_database()
    with database.connection_engine().begin() as connection:
        connection.execute(text("CREATE TABLE sample (value INTEGER NOT NULL)"))
    with pytest.raises(RuntimeError):
        with database.transaction() as session:
            session.execute(text("INSERT INTO sample (value) VALUES (:value)"), {"value": 3})
            raise RuntimeError("owner operation failed")
    with database.session() as session:
        assert session.scalar(text("SELECT count(*) FROM sample")) == 0


def test_file_sqlite_database_is_created(tmp_path: Path) -> None:
    path = tmp_path / "development.db"
    database = started_database(f"sqlite+pysqlite:///{path.as_posix()}")
    assert path.is_file()
    database.shutdown()


def test_unsupported_provider_fails_without_echoing_connection_string() -> None:
    database = DatabaseEngine()
    database.initialize(database_container("mysql://user:private-password@example.invalid/db"))
    with pytest.raises(DatabaseUnavailable) as error:
        database.start()
    assert "private-password" not in str(error.value)


def test_unavailable_postgresql_is_controlled_and_redacted() -> None:
    database = DatabaseEngine()
    database.initialize(
        database_container(
            "postgresql+psycopg://user:private-password@127.0.0.1:1/favorite?connect_timeout=1"
        )
    )
    with pytest.raises(DatabaseUnavailable) as error:
        database.start()
    assert "private-password" not in str(error.value)
