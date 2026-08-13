"""Provider-neutral deployment preflight; it performs no deployment mutation."""
from dataclasses import dataclass

from backend.config import Configuration, SecretValue
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine
from backend.operations.health import HealthEngine
from backend.engines.storage import StorageEngine


@dataclass(frozen=True)
class DeploymentReport:
    valid: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]


class DeploymentValidator:
    def __init__(self, configuration: Configuration, database: DatabaseEngine,
                 migrations: DatabaseMigrationEngine, storage: StorageEngine, health: HealthEngine) -> None:
        self._configuration = configuration; self._database = database; self._migrations = migrations; self._storage = storage; self._health = health

    def validate_production(self) -> DeploymentReport:
        checks: list[str] = []; failures: list[str] = []
        if self._configuration.get("environment", str) == "production": checks.append("environment")
        else: failures.append("environment")
        if not self._configuration.get("debug", bool): checks.append("debug_disabled")
        else: failures.append("debug_disabled")
        if self._database.provider == "postgresql": checks.append("postgresql")
        else: failures.append("postgresql")
        if self._storage.healthcheck() and self._storage.provider_name != "local": checks.append("production_storage")
        else: failures.append("production_storage")
        try:
            if self._configuration.get("authentication.jwt_secret", SecretValue).reveal(): checks.append("authentication_secret")
            else: failures.append("authentication_secret")
        except Exception: failures.append("authentication_secret")
        try:
            if not self._migrations.pending(): checks.append("migrations")
            else: failures.append("migrations")
        except Exception: failures.append("migrations")
        if self._health.readiness().ready: checks.append("readiness")
        else: failures.append("readiness")
        return DeploymentReport(not failures, tuple(checks), tuple(failures))
