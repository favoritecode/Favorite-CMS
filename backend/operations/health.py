"""Provider-neutral health, readiness, and diagnostic contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable

from backend.core.container import ServiceContainer
from backend.core.engine_manager import EngineManager
from backend.core.contracts.engine import EngineLifecycle
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine
from backend.engines.api import APIEngine, APIOperation
from backend.engines.authentication import AuthenticationEngine
from backend.engines.cache import CacheEngine
from backend.engines.plugins import PluginEngine
from backend.engines.queue import QueueEngine
from backend.engines.routing import RouteDefinition, RouteType
from backend.engines.scheduler import SchedulerEngine
from backend.engines.storage import StorageEngine
from backend.engines.themes import ThemeEngine


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ComponentHealth:
    component: str
    status: HealthStatus
    critical: bool


@dataclass(frozen=True)
class HealthReport:
    live: bool
    ready: bool
    status: HealthStatus
    components: tuple[ComponentHealth, ...] = ()


@dataclass(frozen=True)
class HealthContributor:
    contributor_id: str
    owner: str
    check: Callable[[], HealthStatus]
    critical: bool = False


class HealthEngine:
    engine_id = "observability"
    dependencies = ("database", "migrations", "storage", "cache", "queue", "scheduler", "authentication", "plugins", "themes", "routing", "api", "update", "recovery")

    def __init__(self) -> None:
        self._container: ServiceContainer | None = None
        self._contributors: dict[str, HealthContributor] = {}
        self._database: DatabaseEngine | None = None; self._migrations: DatabaseMigrationEngine | None = None
        self._storage: StorageEngine | None = None; self._cache: CacheEngine | None = None; self._queue: QueueEngine | None = None
        self._scheduler: SchedulerEngine | None = None; self._authentication: AuthenticationEngine | None = None
        self._themes: ThemeEngine | None = None; self._engines: EngineManager | None = None; self._api: APIEngine | None = None
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._container = container
        self._database = container.resolve("engine.database", DatabaseEngine); self._migrations = container.resolve("engine.migrations", DatabaseMigrationEngine)
        self._storage = container.resolve("engine.storage", StorageEngine); self._cache = container.resolve("engine.cache", CacheEngine)
        self._queue = container.resolve("engine.queue", QueueEngine); self._scheduler = container.resolve("engine.scheduler", SchedulerEngine)
        self._authentication = container.resolve("engine.authentication", AuthenticationEngine); self._themes = container.resolve("engine.themes", ThemeEngine)
        self._engines = container.resolve("core.engines", EngineManager); self._api = container.resolve("engine.api", APIEngine)
        container.register("engine.observability", self)
        container.resolve("engine.plugins", PluginEngine).publish_phase_service("engine.observability", self)

    def start(self) -> None:
        assert self._api is not None
        self._api.register(RouteDefinition("health.live", "engine.observability", RouteType.API, "/health/live", ("GET",), "health.live"),
                           APIOperation("health.live", "engine.observability", _empty, lambda request, data: self.public_liveness(), lambda value: value))
        self._api.register(RouteDefinition("health.ready", "engine.observability", RouteType.API, "/health/ready", ("GET",), "health.ready"),
                           APIOperation("health.ready", "engine.observability", _empty, lambda request, data: self.public_readiness(), lambda value: value))
        self.ready = True

    def shutdown(self) -> None: self.ready = False; self._contributors.clear()

    def register(self, contributor: HealthContributor) -> None:
        if not contributor.contributor_id.strip() or not contributor.owner.strip() or contributor.contributor_id in self._contributors:
            raise ValueError("Health contributor is invalid or duplicated")
        self._contributors[contributor.contributor_id] = contributor

    def unregister_owner(self, owner: str) -> None:
        for key in tuple(self._contributors):
            if self._contributors[key].owner == owner: del self._contributors[key]

    def for_plugin(self, plugin_id: str) -> "PluginHealth": return PluginHealth(self, plugin_id)

    def liveness(self) -> HealthReport:
        return HealthReport(self.ready, False, HealthStatus.HEALTHY if self.ready else HealthStatus.UNAVAILABLE)

    def readiness(self, *, details: bool = False) -> HealthReport:
        checks = [
            ComponentHealth("database", HealthStatus.HEALTHY if self._database and self._database.healthcheck() else HealthStatus.UNAVAILABLE, True),
            ComponentHealth("storage", HealthStatus.HEALTHY if self._storage and self._storage.healthcheck() else HealthStatus.UNAVAILABLE, True),
            ComponentHealth("migrations", self._migration_health(), True),
            ComponentHealth("authentication", HealthStatus.HEALTHY if self._authentication and self._authentication.ready else HealthStatus.UNAVAILABLE, True),
            ComponentHealth("queue", HealthStatus.HEALTHY if self._queue and self._queue.healthcheck() else HealthStatus.UNAVAILABLE, True),
            ComponentHealth("scheduler", HealthStatus.HEALTHY if self._scheduler and self._scheduler.ready else HealthStatus.UNAVAILABLE, True),
            ComponentHealth("cache", HealthStatus.HEALTHY if self._cache and self._cache.healthcheck() else HealthStatus.DEGRADED, False),
            ComponentHealth("theme", HealthStatus.HEALTHY if self._themes and self._themes.active_theme else HealthStatus.UNAVAILABLE, True),
            ComponentHealth("engines", self._engine_health(), True),
        ]
        for item in tuple(self._contributors.values()):
            try: status = item.check()
            except Exception: status = HealthStatus.UNAVAILABLE if item.critical else HealthStatus.DEGRADED
            checks.append(ComponentHealth(item.contributor_id, status, item.critical))
        unavailable = any(item.critical and item.status is HealthStatus.UNAVAILABLE for item in checks)
        degraded = any(item.status is not HealthStatus.HEALTHY for item in checks)
        status = HealthStatus.UNAVAILABLE if unavailable else HealthStatus.DEGRADED if degraded else HealthStatus.HEALTHY
        return HealthReport(self.ready, self.ready and not unavailable, status, tuple(checks) if details else ())

    def public_liveness(self) -> dict[str, object]:
        report = self.liveness(); return {"status": report.status.value, "live": report.live}

    def public_readiness(self) -> dict[str, object]:
        report = self.readiness(); return {"status": report.status.value, "ready": report.ready}

    def operator_diagnostics(self) -> dict[str, object]:
        """Compose an authorized, value-redacted operational view from owning contracts."""
        from backend.config import Configuration
        from backend.engines.content import ContentEngine
        from backend.engines.media import MediaEngine
        from backend.engines.notifications import NotificationEngine
        from backend.operations.installation import InstallationEngine
        from backend.recovery import BackupRecoveryEngine
        from backend.update import UpdateEngine

        report = self.readiness(details=True)
        components = [{
            "name": item.component,
            "status": item.status.value,
            "critical": item.critical,
            "message": _component_message(item.component, item.status),
        } for item in report.components]
        configuration = self._resolve("core.configuration", Configuration)
        migrations = self._migrations
        try:
            applied = len(migrations.applied()) if migrations else None
            pending = len(migrations.pending()) if migrations else None
            migration_status = "healthy" if pending == 0 else "unavailable"
        except Exception:
            applied = pending = None; migration_status = "unavailable"
        database_provider = self._database.provider if self._database else "unknown"
        selected_storage = configuration.snapshot().get("storage.provider", "unknown") if configuration else "unknown"
        notification = self._resolve("engine.notifications", NotificationEngine)
        installation = self._resolve("engine.installation", InstallationEngine)
        recovery = self._resolve("engine.recovery", BackupRecoveryEngine)
        update = self._resolve("engine.update", UpdateEngine)
        content = self._resolve("engine.content", ContentEngine)
        media = self._resolve("engine.media", MediaEngine)
        return {
            "version": "0.1.0",
            "status": report.status.value,
            "components": components,
            "configuration": {
                "database": "configured" if configuration and configuration.is_configured("database.url") else "missing",
                "database_provider": database_provider,
                "storage": "configured" if configuration and configuration.is_configured("storage.root") else "missing",
                "storage_provider": selected_storage,
                "authentication": "configured" if configuration and configuration.is_configured("authentication.jwt_secret") else "missing",
                "active_theme": "configured" if configuration and configuration.is_configured("theme.active") else "not_configured",
            },
            "migration": {"status": migration_status, "applied": applied, "pending": pending, "mode": "explicit"},
            "installation": installation.operational_status() if installation else {"status": "unknown"},
            "update": update.operational_status() if update else {"status": "unknown"},
            "recovery": recovery.operational_status() if recovery else {"status": "unknown"},
            "notification": dict(notification.operational_status()) if notification else {"status": "unknown"},
            "queue": {"status": "healthy" if self._queue and self._queue.healthcheck() else "unavailable"},
            "scheduler": {"status": "healthy" if self._scheduler and self._scheduler.ready else "unavailable"},
            "content": {"status": "healthy" if content and content.ready else "unavailable", "seo_projection": True},
            "media": {"status": "healthy" if media and media.ready else "unavailable", "supported": "text_document"},
            "theme": {"status": "healthy" if self._themes and self._themes.active_theme else "unavailable",
                      "active": self._themes.active_theme if self._themes else None},
        }

    def _resolve(self, key: str, expected_type):
        if self._container is None or not self._container.contains(key): return None
        try: return self._container.resolve(key, expected_type)
        except Exception: return None

    def _migration_health(self) -> HealthStatus:
        try: return HealthStatus.HEALTHY if self._migrations and not self._migrations.pending() else HealthStatus.UNAVAILABLE
        except Exception: return HealthStatus.UNAVAILABLE

    def _engine_health(self) -> HealthStatus:
        if self._engines is None: return HealthStatus.UNAVAILABLE
        allowed = {EngineLifecycle.STARTED}
        return HealthStatus.HEALTHY if all(state in allowed for _, state in self._engines.states()) else HealthStatus.UNAVAILABLE


class PluginHealth:
    def __init__(self, engine: HealthEngine, plugin_id: str) -> None: self._engine = engine; self._plugin_id = plugin_id
    def register(self, contributor_id: str, check: Callable[[], HealthStatus]) -> None:
        self._engine.register(HealthContributor(contributor_id, self._plugin_id, check, False))
    def unregister_all(self) -> None: self._engine.unregister_owner(self._plugin_id)


def _empty(query, body):
    if query or body is not None: raise ValueError("Health request contains unsupported input")
    return None


def _component_message(component: str, status: HealthStatus) -> str:
    if status is HealthStatus.HEALTHY: return f"{component.title()} is available."
    if status is HealthStatus.DEGRADED: return f"{component.title()} is optional or degraded."
    return f"{component.title()} is required but unavailable."
