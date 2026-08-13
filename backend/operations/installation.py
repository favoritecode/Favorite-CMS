"""Repeatable first-run installation orchestration over owning Engine contracts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from threading import Lock

from sqlalchemy import Column, MetaData, String, Table, insert, select, update

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.authentication import AuthenticationEngine
from backend.engines.permissions import AuthorizationContext, PermissionEngine
from backend.engines.storage import StorageEngine
from backend.engines.themes import ThemeEngine
from backend.engines.users import UserEngine
from backend.operations.health import HealthEngine


class InstallationState(StrEnum):
    UNINSTALLED = "uninstalled"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"


class InstallationError(RuntimeError): pass


@dataclass(frozen=True)
class RequiredAuthorization:
    permission_id: str
    action: str
    resource_type: str


@dataclass(frozen=True, repr=False)
class InstallationRequest:
    email: str
    display_name: str
    password: str
    role: str
    required_authorizations: tuple[RequiredAuthorization, ...]

    def __repr__(self) -> str: return "InstallationRequest('[REDACTED]')"


_metadata = MetaData()
_state = Table("favorite_installation_state", _metadata,
    Column("installation_id", String(32), primary_key=True), Column("state", String(32), nullable=False),
    Column("version", String(64), nullable=False), Column("updated_at", String(64), nullable=False),
    Column("failure", String(64)))


def installation_migration() -> Migration:
    return Migration("platform.installation.001", "platform.installation", lambda connection: _metadata.create_all(connection, tables=[_state]))


class InstallationEngine:
    engine_id = "installation"
    dependencies = ("database", "migrations", "storage", "users", "authentication", "permissions", "plugins", "themes", "observability")

    def __init__(self, version: str = "0.1.0") -> None:
        self._version = version; self._lock = Lock(); self.ready = False
        self._database: DatabaseEngine | None = None; self._migrations: DatabaseMigrationEngine | None = None
        self._storage: StorageEngine | None = None; self._users: UserEngine | None = None; self._auth: AuthenticationEngine | None = None
        self._permissions: PermissionEngine | None = None; self._themes: ThemeEngine | None = None; self._health: HealthEngine | None = None

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine); self._migrations = container.resolve("engine.migrations", DatabaseMigrationEngine)
        self._storage = container.resolve("engine.storage", StorageEngine); self._users = container.resolve("engine.users", UserEngine)
        self._auth = container.resolve("engine.authentication", AuthenticationEngine); self._permissions = container.resolve("engine.permissions", PermissionEngine)
        self._themes = container.resolve("engine.themes", ThemeEngine); self._health = container.resolve("engine.observability", HealthEngine)
        self._migrations.register(installation_migration()); container.register("engine.installation", self)

    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False

    def state(self) -> InstallationState:
        try:
            with self._database_required().session() as session:
                row = session.execute(select(_state).where(_state.c.installation_id == "platform")).mappings().one_or_none()
            return InstallationState.UNINSTALLED if row is None else InstallationState(row["state"])
        except Exception: return InstallationState.UNINSTALLED

    def operational_status(self) -> dict[str, object]:
        return {"status": self.state().value, "version": self._version,
                "automatic_install": False, "automatic_migration": False}

    def install(self, request: InstallationRequest) -> InstallationState:
        if not self._lock.acquire(blocking=False): raise InstallationError("Installation is already active")
        try:
            if self.state() is InstallationState.INSTALLED: return InstallationState.INSTALLED
            self._preflight(request)
            self._write_state(InstallationState.INSTALLING)
            try:
                user = self._users_required().find_by_email(request.email)
                if user is None:
                    user = self._users_required().create(email=request.email, display_name=request.display_name, role=request.role)
                    self._auth_required().set_password(user.user_id, request.password)
                elif user.role != request.role:
                    raise InstallationError("Initial identity does not match partial installation state")
                login = self._auth_required().login(email=request.email, password=request.password)
                if not login.success: raise InstallationError("Initial identity verification failed")
                for required in request.required_authorizations:
                    self._permissions_required().require(required.permission_id, AuthorizationContext(required.action, required.resource_type, login.context))
                if self._themes_required().active_theme is None: raise InstallationError("An active Theme is required")
                if not self._health_required().readiness().ready: raise InstallationError("Installation readiness validation failed")
                self._write_state(InstallationState.INSTALLED)
                return InstallationState.INSTALLED
            except Exception as exc:
                self._write_state(InstallationState.FAILED, type(exc).__name__)
                if isinstance(exc, InstallationError): raise
                raise InstallationError("Installation failed") from exc
        finally: self._lock.release()

    def _preflight(self, request: InstallationRequest) -> None:
        if not self.ready or not self._database_required().healthcheck() or not self._storage_required().healthcheck():
            raise InstallationError("Installation preflight failed")
        if not request.email.strip() or not request.display_name.strip() or len(request.password) < 12 or not request.role.strip() or not request.required_authorizations:
            raise InstallationError("Installation request is invalid")
        self._migrations_required().initialize_history(); self._migrations_required().upgrade()

    def _write_state(self, state: InstallationState, failure: str | None = None) -> None:
        values = {"state": state.value, "version": self._version, "updated_at": datetime.now(timezone.utc).isoformat(), "failure": failure}
        with self._database_required().transaction() as session:
            current = session.execute(select(_state.c.installation_id).where(_state.c.installation_id == "platform")).scalar_one_or_none()
            session.execute(update(_state).where(_state.c.installation_id == "platform").values(**values) if current else insert(_state).values(installation_id="platform", **values))

    def _database_required(self):
        if self._database is None: raise InstallationError("Database is unavailable")
        return self._database
    def _migrations_required(self):
        if self._migrations is None: raise InstallationError("Migrations are unavailable")
        return self._migrations
    def _storage_required(self):
        if self._storage is None: raise InstallationError("Storage is unavailable")
        return self._storage
    def _users_required(self):
        if self._users is None: raise InstallationError("Users are unavailable")
        return self._users
    def _auth_required(self):
        if self._auth is None: raise InstallationError("Authentication is unavailable")
        return self._auth
    def _permissions_required(self):
        if self._permissions is None: raise InstallationError("Permission is unavailable")
        return self._permissions
    def _themes_required(self):
        if self._themes is None: raise InstallationError("Themes are unavailable")
        return self._themes
    def _health_required(self):
        if self._health is None: raise InstallationError("Health is unavailable")
        return self._health
