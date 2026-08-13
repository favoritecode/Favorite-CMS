"""Application-managed Settings, deliberately separate from bootstrap Configuration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from typing import Callable
from uuid import UUID

from sqlalchemy import Column, MetaData, String, Table, Text, delete, insert, select, update

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.authentication import AuthenticationContext
from backend.engines.cache import CacheEngine, CacheScope
from backend.engines.data_contracts import identifier
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.permissions import AuthorizationContext, PermissionEngine


class SettingsError(ApplicationFailure): pass
class InvalidSetting(ValidationFailure): pass


class SettingScopeKind(StrEnum):
    PLATFORM = "platform"
    ENGINE = "engine"
    THEME = "theme"
    PLUGIN = "plugin"
    USER = "user"


@dataclass(frozen=True)
class SettingScope:
    kind: SettingScopeKind
    owner: str
    subject: str = "default"

    def __post_init__(self) -> None:
        identifier(self.owner, "Setting owner")
        if self.kind is SettingScopeKind.USER:
            try: UUID(self.subject)
            except (ValueError, TypeError) as exc: raise InvalidSetting("User Setting subject is invalid") from exc
        else:
            identifier(self.subject, "Setting subject")


_MISSING = object()
Validator = Callable[[object], None]


@dataclass(frozen=True)
class SettingDefinition:
    key: str
    owner: str
    scope_kind: SettingScopeKind
    value_type: type[bool] | type[str] | type[int] | type[float] | type[dict] | type[list]
    default: object = _MISSING
    validator: Validator | None = None
    sensitive: bool = False
    mutable: bool = True
    read_permission: str | None = None
    write_permission: str | None = None

    def __post_init__(self) -> None:
        identifier(self.key, "Setting Key"); identifier(self.owner, "Setting owner")
        if self.value_type not in {bool, str, int, float, dict, list}:
            raise InvalidSetting("Setting value type is unsupported")
        if self.sensitive and self.read_permission is None:
            raise InvalidSetting("Sensitive Setting requires read authorization")
        if self.default is not _MISSING: _validate_value(self, self.default)


class ProtectedSettingValue:
    __slots__ = ("_value",)
    def __init__(self, value: object) -> None: self._value = value
    def reveal(self) -> object: return self._value
    def __repr__(self) -> str: return "ProtectedSettingValue('[REDACTED]')"
    def __str__(self) -> str: return "[REDACTED]"


@dataclass(frozen=True)
class SettingResult:
    key: str
    scope: SettingScope
    value: object
    customized: bool


_metadata = MetaData()
_settings = Table(
    "favorite_settings", _metadata,
    Column("scope_kind", String(32), primary_key=True), Column("scope_owner", String(255), primary_key=True),
    Column("scope_subject", String(255), primary_key=True), Column("setting_key", String(255), primary_key=True),
    Column("setting_value", Text, nullable=False),
)


def settings_migration() -> Migration:
    return Migration("platform.settings.001", "engine.settings",
                     lambda connection: _metadata.create_all(connection, tables=[_settings]))


class SettingsEngine:
    engine_id = "settings"
    dependencies = ("database", "migrations", "permissions", "cache")

    def __init__(self) -> None:
        self._definitions: dict[tuple[SettingScopeKind, str, str], SettingDefinition] = {}
        self._database: DatabaseEngine | None = None; self._permissions: PermissionEngine | None = None
        self._cache: CacheEngine | None = None; self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        self._cache = container.resolve("engine.cache", CacheEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(settings_migration())
        container.register("engine.settings", self)
    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False

    def register(self, definition: SettingDefinition) -> None:
        key = (definition.scope_kind, definition.owner, definition.key)
        if key in self._definitions: raise InvalidSetting("Setting is already registered")
        self._definitions[key] = definition

    def unregister(self, key: str, scope_kind: SettingScopeKind, owner: str) -> None:
        """Remove the active definition while preserving stored values for migration."""
        try: del self._definitions[(scope_kind, owner, key)]
        except KeyError as exc: raise InvalidSetting("Setting is not registered") from exc

    def get(self, key: str, scope: SettingScope,
            authentication: AuthenticationContext | None = None) -> SettingResult:
        definition = self._definition(key, scope)
        self._authorize(definition.read_permission, "read", scope, authentication)
        with self._db().session() as session:
            stored = session.execute(select(_settings.c.setting_value).where(_where(scope, key))).scalar_one_or_none()
        if stored is None:
            if definition.default is _MISSING: raise SettingsError("Setting Value is unavailable")
            value, customized = definition.default, False
        else:
            try: value, customized = json.loads(stored), True; _validate_value(definition, value)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                raise SettingsError("Stored Setting Value is invalid") from exc
        exposed = ProtectedSettingValue(value) if definition.sensitive else value
        return SettingResult(definition.key, scope, exposed, customized)

    def set(self, key: str, scope: SettingScope, value: object,
            authentication: AuthenticationContext | None = None) -> SettingResult:
        definition = self._definition(key, scope)
        if not definition.mutable: raise SettingsError("Setting is immutable")
        self._authorize(definition.write_permission, "update", scope, authentication)
        _validate_value(definition, value); encoded = json.dumps(value, separators=(",", ":"), sort_keys=True)
        with self._db().transaction() as session:
            existing = session.execute(select(_settings.c.setting_key).where(_where(scope, key))).scalar_one_or_none()
            values = _scope_values(scope, key, encoded)
            if existing is None: session.execute(insert(_settings).values(**values))
            else: session.execute(update(_settings).where(_where(scope, key)).values(setting_value=encoded))
        self._invalidate(scope); return self.get(key, scope, authentication)

    def reset(self, key: str, scope: SettingScope,
              authentication: AuthenticationContext | None = None) -> SettingResult:
        definition = self._definition(key, scope)
        self._authorize(definition.write_permission, "reset", scope, authentication)
        with self._db().transaction() as session: session.execute(delete(_settings).where(_where(scope, key)))
        self._invalidate(scope); return self.get(key, scope, authentication)

    def _definition(self, key: str, scope: SettingScope) -> SettingDefinition:
        try: definition = self._definitions[(scope.kind, scope.owner, key)]
        except KeyError as exc: raise InvalidSetting("Setting is not registered") from exc
        return definition
    def _authorize(self, permission_id: str | None, action: str, scope: SettingScope,
                   authentication: AuthenticationContext | None) -> None:
        if permission_id is None: return
        self._permissions_required().require(permission_id, AuthorizationContext(
            action, "setting", authentication, f"{scope.kind.value}:{scope.owner}:{scope.subject}",
            scope.subject if scope.kind is SettingScopeKind.USER else None))
    def _db(self) -> DatabaseEngine:
        if not self.ready or self._database is None: raise SettingsError("Settings Engine is unavailable")
        return self._database
    def _permissions_required(self) -> PermissionEngine:
        if self._permissions is None: raise SettingsError("Permission service is unavailable")
        return self._permissions
    def _invalidate(self, scope: SettingScope) -> None:
        if self._cache is not None: self._cache.clear(CacheScope(scope.kind.value, f"settings.{scope.owner}"))


def _validate_value(definition: SettingDefinition, value: object) -> None:
    if definition.value_type is int:
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif definition.value_type is float:
        valid = isinstance(value, (int, float)) and not isinstance(value, bool)
    else: valid = isinstance(value, definition.value_type)
    if not valid: raise InvalidSetting("Setting Value has an invalid type")
    try: json.dumps(value)
    except TypeError as exc: raise InvalidSetting("Setting Value is not serializable") from exc
    if definition.validator is not None: definition.validator(value)
def _where(scope: SettingScope, key: str):
    return (_settings.c.scope_kind == scope.kind.value) & (_settings.c.scope_owner == scope.owner) & (_settings.c.scope_subject == scope.subject) & (_settings.c.setting_key == key)
def _scope_values(scope: SettingScope, key: str, value: str) -> dict[str, str]:
    return {"scope_kind": scope.kind.value, "scope_owner": scope.owner, "scope_subject": scope.subject,
            "setting_key": key, "setting_value": value}
