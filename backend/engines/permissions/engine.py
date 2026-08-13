"""Explicit, deterministic authorization with no built-in role matrix."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Column, MetaData, String, Table, insert, select

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.authentication import AuthenticationContext, AuthenticationEngine
from backend.engines.users import UserEngine


class PermissionError(ValidationFailure):
    pass


class PermissionDenied(ApplicationFailure):
    pass


@dataclass(frozen=True)
class PermissionDefinition:
    permission_id: str
    owner: str
    action: str
    resource_type: str
    allow_owner: bool = False
    allow_public: bool = False

    def __post_init__(self) -> None:
        values = (self.permission_id, self.owner, self.action, self.resource_type)
        if any(not item.strip() for item in values):
            raise PermissionError("Permission definition is invalid")


@dataclass(frozen=True)
class RoleGrant:
    role: str
    permission_id: str
    owner: str

    def __post_init__(self) -> None:
        if not self.role.strip() or not self.permission_id.strip() or not self.owner.strip():
            raise PermissionError("Role grant is invalid")


@dataclass(frozen=True)
class AuthorizationContext:
    action: str
    resource_type: str
    authentication: AuthenticationContext | None = None
    resource_id: str | None = None
    owner_user_id: str | None = None
    public: bool = False


@dataclass(frozen=True)
class PermissionDecision:
    permission_id: str
    allowed: bool
    reason: str


_metadata = MetaData()
_role_grants = Table("favorite_permission_role_grants", _metadata,
    Column("role", String(255), primary_key=True), Column("permission_id", String(255), primary_key=True),
    Column("owner", String(255), nullable=False))


def permission_migration() -> Migration:
    return Migration("platform.permission.001", "engine.permissions", lambda connection: _metadata.create_all(connection, tables=[_role_grants]))


class PermissionEngine:
    engine_id = "permissions"
    dependencies = ("users", "authentication", "database", "migrations")

    def __init__(self) -> None:
        self._definitions: dict[str, PermissionDefinition] = {}
        self._grants: set[tuple[str, str]] = set()
        self._users: UserEngine | None = None
        self._authentication: AuthenticationEngine | None = None
        self._database: DatabaseEngine | None = None
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._users = container.resolve("engine.users", UserEngine)
        self._authentication = container.resolve("engine.authentication", AuthenticationEngine)
        self._database = container.resolve("engine.database", DatabaseEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(permission_migration())
        container.register("engine.permissions", self)

    def start(self) -> None:
        if self._database is not None:
            try:
                with self._database.session() as session:
                    self._grants.update((str(row.role), str(row.permission_id)) for row in session.execute(select(_role_grants)).all())
            except Exception:
                pass
        self.ready = True

    def shutdown(self) -> None:
        self.ready = False

    def register(self, definition: PermissionDefinition) -> None:
        if definition.permission_id in self._definitions:
            raise PermissionError("Permission is already registered")
        self._definitions[definition.permission_id] = definition

    def grant_role(self, grant: RoleGrant) -> None:
        definition = self._definitions.get(grant.permission_id)
        if definition is None:
            raise PermissionError("Permission is not registered")
        if definition.owner != grant.owner:
            raise PermissionError("Permission owner does not match the grant owner")
        self._grants.add((grant.role, grant.permission_id))
        if self._database is not None:
            with self._database.transaction() as session:
                existing = session.execute(select(_role_grants.c.role).where(
                    (_role_grants.c.role == grant.role) & (_role_grants.c.permission_id == grant.permission_id))).scalar_one_or_none()
                if existing is None:
                    session.execute(insert(_role_grants).values(role=grant.role, permission_id=grant.permission_id, owner=grant.owner))

    def evaluate(self, permission_id: str, context: AuthorizationContext) -> PermissionDecision:
        if not self.ready:
            return PermissionDecision(permission_id, False, "permission_engine_unavailable")
        definition = self._definitions.get(permission_id)
        if definition is None:
            return PermissionDecision(permission_id, False, "unknown_permission")
        if not context.action.strip() or not context.resource_type.strip():
            return PermissionDecision(permission_id, False, "invalid_context")
        if context.action != definition.action or context.resource_type != definition.resource_type:
            return PermissionDecision(permission_id, False, "context_mismatch")
        if context.public and definition.allow_public:
            return PermissionDecision(permission_id, True, "public_rule")
        authentication = context.authentication
        if authentication is None or not self._authentication_required().is_context_valid(authentication):
            return PermissionDecision(permission_id, False, "authentication_required")
        if authentication.user_id is None:
            return PermissionDecision(permission_id, False, "authentication_required")
        user = self._users_required().get(authentication.user_id)
        if (
            definition.allow_owner
            and context.owner_user_id is not None
            and context.owner_user_id == user.user_id
        ):
            return PermissionDecision(permission_id, True, "ownership_rule")
        if (user.role, permission_id) in self._grants:
            return PermissionDecision(permission_id, True, "role_grant")
        return PermissionDecision(permission_id, False, "not_granted")

    def require(self, permission_id: str, context: AuthorizationContext) -> PermissionDecision:
        decision = self.evaluate(permission_id, context)
        if not decision.allowed:
            raise PermissionDenied("Permission denied")
        return decision

    def _users_required(self) -> UserEngine:
        if self._users is None:
            raise PermissionError("User context is unavailable")
        return self._users

    def _authentication_required(self) -> AuthenticationEngine:
        if self._authentication is None:
            raise PermissionError("Authentication context is unavailable")
        return self._authentication
