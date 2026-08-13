from backend.config import ConfigField, Configuration, ConfigurationSchema, MappingSource
from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine


def database_container(url: str = "sqlite+pysqlite:///:memory:") -> ServiceContainer:
    schema = ConfigurationSchema((ConfigField("database.url", str, required=True, secret=True),))
    configuration = Configuration.resolve(
        schema, (MappingSource("test", {"database.url": url}, priority=1),)
    )
    container = ServiceContainer()
    container.register("core.configuration", configuration)
    return container


def started_database(url: str = "sqlite+pysqlite:///:memory:") -> DatabaseEngine:
    database = DatabaseEngine()
    database.initialize(database_container(url))
    database.start()
    return database

