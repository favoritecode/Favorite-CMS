from pathlib import Path

from backend.bootstrap import build_kernel
from backend.config import ConfigField, Configuration, ConfigurationSchema, MappingSource
from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.cache import CacheEngine
from backend.engines.logging import LoggingEngine
from backend.engines.storage import StorageEngine


def test_core_bootstraps_phase2_infrastructure_and_shuts_down() -> None:
    kernel = build_kernel()
    kernel.bootstrap()
    database = kernel.container.resolve("engine.database", DatabaseEngine)
    migrations = kernel.container.resolve("engine.migrations", DatabaseMigrationEngine)
    storage = kernel.container.resolve("engine.storage", StorageEngine)
    cache = kernel.container.resolve("engine.cache", CacheEngine)
    assert kernel.ready
    assert database.ready and database.healthcheck()
    assert migrations.ready
    assert storage.ready
    assert cache.ready
    kernel.shutdown()
    assert not database.ready
    assert not migrations.ready
    assert not storage.ready
    assert not cache.ready


def test_phase2_engines_consume_configuration_contract(tmp_path: Path) -> None:
    schema = ConfigurationSchema(
        (
            ConfigField("database.url", str, required=True, secret=True),
            ConfigField("storage.root", str, required=True, secret=True),
            ConfigField("cache.enabled", bool, required=True),
        )
    )
    configuration = Configuration.resolve(
        schema,
        (
            MappingSource(
                "test",
                {
                    "database.url": "sqlite+pysqlite:///:memory:",
                    "storage.root": "storage/test-phase2",
                    "cache.enabled": False,
                },
                1,
            ),
        ),
    )
    container = ServiceContainer()
    container.register("core.configuration", configuration)
    container.register("core.logging", LoggingEngine())
    database = DatabaseEngine()
    database.initialize(container)
    database.start()
    storage = StorageEngine()
    storage.initialize(container)
    storage.start()
    cache = CacheEngine()
    cache.initialize(container)
    cache.start()
    assert database.provider == "sqlite"
    assert storage.ready
    assert cache.ready

