"""Explicit, deterministic authorization with no built-in role matrix."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Boolean, Column, MetaData, String, Table, delete, insert, select, update

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
class RoleDefinition:
    role_id: str
    name: str
    built_in: bool = False

    def __post_init__(self) -> None:
        if not self.role_id.strip() or not self.name.strip() or len(self.role_id) > 255 or len(self.name) > 255:
            raise PermissionError("Role definition is invalid")


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
_roles = Table("favorite_permission_roles", _metadata,
    Column("role_id", String(255), primary_key=True), Column("name", String(255), nullable=False),
    Column("built_in", Boolean, nullable=False, default=False))


def permission_migration() -> Migration:
    return Migration("platform.permission.001", "engine.permissions", lambda connection: _metadata.create_all(connection, tables=[_role_grants]))


def permission_roles_migration() -> Migration:
    def upgrade(connection) -> None:
        _metadata.create_all(connection, tables=[_roles])
        for role_id, name in (("site-owner", "Site Owner"), ("admin", "Legacy Administrator")):
            if connection.execute(select(_roles.c.role_id).where(_roles.c.role_id == role_id)).scalar_one_or_none() is None:
                connection.execute(insert(_roles).values(role_id=role_id, name=name, built_in=True))
    return Migration("platform.permission.002", "engine.permissions", upgrade, dependencies=("platform.permission.001",))


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
        migrations = container.resolve("engine.migrations", DatabaseMigrationEngine)
        migrations.register(permission_migration())
        migrations.register(permission_roles_migration())
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

    def unregister_owner(self, owner: str) -> None:
        """Remove active definitions while preserving durable grants for safe reactivation."""
        self._definitions = {key: value for key, value in self._definitions.items() if value.owner != owner}

    def for_plugin(self, plugin_id: str) -> "PluginPermissions": return PluginPermissions(self, plugin_id)

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

    def definitions(self) -> tuple[PermissionDefinition, ...]:
        return tuple(self._definitions[key] for key in sorted(self._definitions))

    def roles(self) -> tuple[RoleDefinition, ...]:
        with self._database_required().session() as session:
            rows = session.execute(select(_roles).order_by(_roles.c.role_id)).mappings().all()
        return tuple(RoleDefinition(str(row["role_id"]), str(row["name"]), bool(row["built_in"])) for row in rows)

    def role(self, role_id: str) -> RoleDefinition | None:
        with self._database_required().session() as session:
            row = session.execute(select(_roles).where(_roles.c.role_id == role_id.strip())).mappings().first()
        return None if row is None else RoleDefinition(str(row["role_id"]), str(row["name"]), bool(row["built_in"]))

    def create_role(self, role: RoleDefinition) -> RoleDefinition:
        if self.role(role.role_id) is not None:
            raise PermissionError("Role already exists")
        with self._database_required().transaction() as session:
            session.execute(insert(_roles).values(role_id=role.role_id, name=role.name, built_in=role.built_in))
        return role

    def rename_role(self, role_id: str, name: str) -> RoleDefinition:
        role = self.role(role_id)
        normalized = name.strip()
        if role is None:
            raise PermissionError("Role was not found")
        if role.built_in:
            raise PermissionError("Built-in roles cannot be renamed")
        if not normalized or len(normalized) > 255:
            raise PermissionError("Role name is invalid")
        with self._database_required().transaction() as session:
            session.execute(update(_roles).where(_roles.c.role_id == role_id).values(name=normalized))
        return RoleDefinition(role.role_id, normalized, role.built_in)

    def delete_role(self, role_id: str) -> None:
        role = self.role(role_id)
        if role is None:
            raise PermissionError("Role was not found")
        if role.built_in:
            raise PermissionError("Built-in roles cannot be deleted")
        with self._database_required().transaction() as session:
            session.execute(delete(_role_grants).where(_role_grants.c.role == role_id))
            session.execute(delete(_roles).where(_roles.c.role_id == role_id))
        self._grants = {grant for grant in self._grants if grant[0] != role_id}

    def role_permissions(self, role_id: str) -> tuple[str, ...]:
        return tuple(sorted(permission_id for role, permission_id in self._grants if role == role_id))

    def set_role_permissions(self, role_id: str, permission_ids: tuple[str, ...]) -> None:
        role = self.role(role_id)
        if role is None:
            raise PermissionError("Role was not found")
        if role.built_in:
            raise PermissionError("Built-in role permissions are release-managed")
        self._replace_role_permissions(role_id, permission_ids)

    def set_release_managed_permissions(self, role_id: str, permission_ids: tuple[str, ...]) -> None:
        """Apply the versioned explicit grants for a built-in role during composition."""
        role = self.role(role_id)
        if role is None or not role.built_in:
            raise PermissionError("Release-managed role was not found")
        self._replace_role_permissions(role_id, permission_ids)

    def _replace_role_permissions(self, role_id: str, permission_ids: tuple[str, ...]) -> None:
        normalized = tuple(dict.fromkeys(permission_ids))
        if any(item not in self._definitions for item in normalized):
            raise PermissionError("Permission is not registered")
        with self._database_required().transaction() as session:
            session.execute(delete(_role_grants).where(_role_grants.c.role == role_id))
            for permission_id in normalized:
                definition = self._definitions[permission_id]
                session.execute(insert(_role_grants).values(role=role_id, permission_id=permission_id, owner=definition.owner))
        self._grants = {grant for grant in self._grants if grant[0] != role_id}
        self._grants.update((role_id, permission_id) for permission_id in normalized)

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
        if any((role, permission_id) in self._grants for role in user.roles or (user.role,)):
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

    def _database_required(self) -> DatabaseEngine:
        if self._database is None:
            raise PermissionError("Permission persistence is unavailable")
        return self._database


class PluginPermissions:
    def __init__(self, engine: PermissionEngine, plugin_id: str) -> None: self._engine = engine; self.plugin_id = plugin_id
    def register(self, definition: PermissionDefinition) -> None:
        if definition.owner != self.plugin_id: raise PermissionError("Plugin cannot register another owner's Permission")
        self._engine.register(definition)
    def unregister_all(self) -> None: self._engine.unregister_owner(self.plugin_id)
