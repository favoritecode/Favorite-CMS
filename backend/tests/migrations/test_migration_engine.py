import pytest
from sqlalchemy import text

from backend.core.container import ServiceContainer
from backend.database.migrations import DatabaseMigrationEngine, Migration, MigrationError
from backend.tests.database.conftest import started_database


def migration_engine() -> tuple[DatabaseMigrationEngine, object]:
    database = started_database()
    container = ServiceContainer()
    container.register("engine.database", database)
    migrations = DatabaseMigrationEngine()
    migrations.initialize(container)
    migrations.start()
    migrations.initialize_history()
    return migrations, database


def test_fresh_upgrade_tracks_version_and_repeated_run_is_empty() -> None:
    migrations, database = migration_engine()
    migrations.register(
        Migration(
            "platform.test.001",
            "platform.test",
            lambda connection: connection.execute(text("CREATE TABLE test_one (id INTEGER PRIMARY KEY)")),
        )
    )
    assert migrations.upgrade() == ("platform.test.001",)
    assert migrations.applied() == ("platform.test.001",)
    assert migrations.upgrade() == ()
    with database.connection_engine().connect() as connection:
        connection.execute(text("SELECT * FROM test_one"))


def test_dependency_order_is_deterministic() -> None:
    migrations, _ = migration_engine()
    calls: list[str] = []
    migrations.register(Migration("b", "test", lambda connection: calls.append("b"), ("a",)))
    migrations.register(Migration("a", "test", lambda connection: calls.append("a")))
    assert migrations.upgrade() == ("a", "b")
    assert calls == ["a", "b"]


def test_invalid_dependency_blocks_migration() -> None:
    migrations, _ = migration_engine()
    migrations.register(Migration("a", "test", lambda connection: None, ("missing",)))
    with pytest.raises(MigrationError, match="unresolved"):
        migrations.upgrade()


def test_failed_migration_is_not_recorded() -> None:
    migrations, _ = migration_engine()

    def fail(connection: object) -> None:
        raise RuntimeError("failure")

    migrations.register(Migration("failed", "test", fail))
    with pytest.raises(MigrationError, match="failed"):
        migrations.upgrade()
    assert migrations.applied() == ()


def test_history_must_be_explicitly_initialized() -> None:
    database = started_database()
    container = ServiceContainer()
    container.register("engine.database", database)
    migrations = DatabaseMigrationEngine()
    migrations.initialize(container)
    migrations.start()
    with pytest.raises(MigrationError, match="history"):
        migrations.applied()


def test_database_connection_failure_stops_migration_startup() -> None:
    from backend.database import DatabaseEngine

    container = ServiceContainer()
    container.register("engine.database", DatabaseEngine())
    migrations = DatabaseMigrationEngine()
    migrations.initialize(container)
    with pytest.raises(MigrationError, match="unavailable"):
        migrations.start()


def test_database_lock_blocks_concurrent_sequence() -> None:
    migrations, database = migration_engine()
    with database.connection_engine().begin() as connection:
        connection.execute(
            text(
                "INSERT INTO favorite_migration_lock (lock_id, acquired_at) "
                "VALUES (:lock_id, :acquired_at)"
            ),
            {"lock_id": "migration-sequence", "acquired_at": "test"},
        )
    with pytest.raises(MigrationError, match="lock"):
        migrations.upgrade()
    with database.connection_engine().connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM favorite_migration_lock")) == 1
