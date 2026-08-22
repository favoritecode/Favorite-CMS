"""Plugin-scoped generic domain records without exposing Database internals."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import StrEnum
import json
import re
from types import MappingProxyType
from typing import Mapping
from uuid import UUID, uuid4

from sqlalchemy import Column, MetaData, String, Table, Text, delete, insert, select, update

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.authentication import AuthenticationContext
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.permissions import AuthorizationContext, PermissionEngine


class DomainError(ApplicationFailure): pass
class InvalidDomain(ValidationFailure): pass


class DomainFieldKind(StrEnum):
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    ENUM = "enum"
    MEDIA = "media"
    RELATION = "relation"


@dataclass(frozen=True)
class DomainField:
    field_id: str
    kind: DomainFieldKind
    required: bool = False
    maximum_length: int | None = None
    choices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _identifier(self.field_id) or not isinstance(self.kind, DomainFieldKind):
            raise InvalidDomain("Domain field is invalid")
        if self.maximum_length is not None and not 1 <= self.maximum_length <= 100_000:
            raise InvalidDomain("Domain field length is invalid")
        if self.kind is DomainFieldKind.ENUM and (not self.choices or len(set(self.choices)) != len(self.choices)):
            raise InvalidDomain("Domain enum choices are invalid")
        if self.kind is not DomainFieldKind.ENUM and self.choices:
            raise InvalidDomain("Domain choices require an enum field")


@dataclass(frozen=True)
class DomainEntityContract:
    entity_type: str
    owner: str
    label: str
    fields: tuple[DomainField, ...]
    permissions: Mapping[str, str]

    def __post_init__(self) -> None:
        if not _identifier(self.entity_type) or not _identifier(self.owner) or not 1 <= len(self.label.strip()) <= 80:
            raise InvalidDomain("Domain entity contract is invalid")
        if not self.fields or len({field.field_id for field in self.fields}) != len(self.fields):
            raise InvalidDomain("Domain entity fields are invalid")
        if set(self.permissions) != {"create", "read", "update", "delete"}:
            raise InvalidDomain("Domain entity permissions are invalid")
        object.__setattr__(self, "permissions", MappingProxyType(dict(self.permissions)))


@dataclass(frozen=True)
class DomainRecord:
    record_id: str
    entity_type: str
    owner: str
    values: Mapping[str, object]
    owner_user_id: str
    created_at: str
    updated_at: str


_metadata = MetaData()
_records = Table("favorite_domain_records", _metadata,
    Column("record_id", String(36), primary_key=True), Column("entity_type", String(255), nullable=False),
    Column("owner", String(255), nullable=False), Column("record_values", Text, nullable=False),
    Column("owner_user_id", String(36), nullable=False), Column("created_at", String(64), nullable=False),
    Column("updated_at", String(64), nullable=False))


def domain_migration() -> Migration:
    return Migration("platform.domain.001", "engine.domains", lambda connection: _metadata.create_all(connection, tables=[_records]),
                     dependencies=("platform.user.001",))


class DomainEngine:
    engine_id = "domains"
    dependencies = ("database", "migrations", "permissions")

    def __init__(self) -> None:
        self._database: DatabaseEngine | None = None; self._permissions: PermissionEngine | None = None
        self._contracts: dict[tuple[str, str], DomainEntityContract] = {}; self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(domain_migration())
        container.register("engine.domains", self)

    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False; self._contracts.clear()
    def for_plugin(self, plugin_id: str) -> "PluginDomains": return PluginDomains(self, plugin_id)

    def register(self, contract: DomainEntityContract) -> None:
        key = (contract.owner, contract.entity_type)
        if key in self._contracts: raise InvalidDomain("Domain entity contract is already registered")
        self._contracts[key] = contract

    def unregister_owner(self, owner: str) -> None:
        for key in tuple(self._contracts):
            if key[0] == owner: del self._contracts[key]

    def contracts(self, owner: str | None = None) -> tuple[DomainEntityContract, ...]:
        values = (item for item in self._contracts.values() if owner is None or item.owner == owner)
        return tuple(sorted(values, key=lambda item: (item.owner, item.entity_type)))

    def create(self, owner: str, entity_type: str, values: Mapping[str, object], authentication: AuthenticationContext) -> DomainRecord:
        contract = self._contract(owner, entity_type); self._authorize(contract, "create", authentication)
        valid = _validate_values(contract, values); now = _now(); identifier = str(uuid4())
        record = DomainRecord(identifier, entity_type, owner, valid, authentication.user_id or "", now, now)
        with self._db().transaction() as session: session.execute(insert(_records).values(**_record_values(record)))
        return record

    def get(self, owner: str, entity_type: str, record_id: str, authentication: AuthenticationContext) -> DomainRecord:
        contract = self._contract(owner, entity_type); record = self._load(owner, entity_type, record_id)
        self._authorize(contract, "read", authentication, record); return record

    def list(self, owner: str, entity_type: str, authentication: AuthenticationContext) -> tuple[DomainRecord, ...]:
        contract = self._contract(owner, entity_type); self._authorize(contract, "read", authentication)
        with self._db().session() as session:
            rows = session.execute(select(_records).where((_records.c.owner == owner) & (_records.c.entity_type == entity_type)).order_by(_records.c.created_at, _records.c.record_id)).mappings()
            return tuple(_from_row(row) for row in rows)

    def update(self, owner: str, entity_type: str, record_id: str, values: Mapping[str, object], authentication: AuthenticationContext) -> DomainRecord:
        contract = self._contract(owner, entity_type); current = self._load(owner, entity_type, record_id)
        self._authorize(contract, "update", authentication, current); valid = _validate_values(contract, values); now = _now()
        with self._db().transaction() as session:
            session.execute(update(_records).where(_records.c.record_id == current.record_id).values(record_values=_dump(valid), updated_at=now))
        return DomainRecord(current.record_id, current.entity_type, current.owner, valid, current.owner_user_id, current.created_at, now)

    def delete(self, owner: str, entity_type: str, record_id: str, authentication: AuthenticationContext) -> None:
        contract = self._contract(owner, entity_type); current = self._load(owner, entity_type, record_id)
        self._authorize(contract, "delete", authentication, current)
        with self._db().transaction() as session: session.execute(delete(_records).where(_records.c.record_id == current.record_id))

    def _contract(self, owner: str, entity_type: str) -> DomainEntityContract:
        try: return self._contracts[(owner, entity_type)]
        except KeyError as exc: raise InvalidDomain("Domain entity contract is unavailable") from exc
    def _load(self, owner: str, entity_type: str, record_id: str) -> DomainRecord:
        try: identifier = str(UUID(record_id))
        except (ValueError, TypeError) as exc: raise InvalidDomain("Domain record identifier is invalid") from exc
        with self._db().session() as session:
            row = session.execute(select(_records).where((_records.c.record_id == identifier) & (_records.c.owner == owner) & (_records.c.entity_type == entity_type))).mappings().first()
        if row is None: raise DomainError("Domain record was not found")
        return _from_row(row)
    def _authorize(self, contract: DomainEntityContract, action: str, authentication: AuthenticationContext, record: DomainRecord | None = None) -> None:
        if self._permissions is None: raise DomainError("Permission service is unavailable")
        self._permissions.require(contract.permissions[action], AuthorizationContext(action, "plugin_domain", authentication,
            record.record_id if record else None, record.owner_user_id if record else None))
    def _db(self) -> DatabaseEngine:
        if not self.ready or self._database is None: raise DomainError("Domain Engine is unavailable")
        return self._database


class PluginDomains:
    def __init__(self, engine: DomainEngine, plugin_id: str) -> None: self._engine = engine; self.plugin_id = plugin_id
    def register(self, contract: DomainEntityContract) -> None:
        if contract.owner != self.plugin_id: raise InvalidDomain("Plugin cannot register another owner's domain")
        self._engine.register(contract)
    def create(self, entity_type: str, values: Mapping[str, object], authentication: AuthenticationContext) -> DomainRecord: return self._engine.create(self.plugin_id, entity_type, values, authentication)
    def get(self, entity_type: str, record_id: str, authentication: AuthenticationContext) -> DomainRecord: return self._engine.get(self.plugin_id, entity_type, record_id, authentication)
    def list(self, entity_type: str, authentication: AuthenticationContext) -> tuple[DomainRecord, ...]: return self._engine.list(self.plugin_id, entity_type, authentication)
    def update(self, entity_type: str, record_id: str, values: Mapping[str, object], authentication: AuthenticationContext) -> DomainRecord: return self._engine.update(self.plugin_id, entity_type, record_id, values, authentication)
    def delete(self, entity_type: str, record_id: str, authentication: AuthenticationContext) -> None: self._engine.delete(self.plugin_id, entity_type, record_id, authentication)
    def unregister_all(self) -> None: self._engine.unregister_owner(self.plugin_id)


def _validate_values(contract: DomainEntityContract, values: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(values, Mapping) or set(values) - {field.field_id for field in contract.fields}: raise InvalidDomain("Domain record contains unknown fields")
    output: dict[str, object] = {}
    for field in contract.fields:
        value = values.get(field.field_id)
        if value is None:
            if field.required: raise InvalidDomain(f"Domain field is required: {field.field_id}")
            continue
        if field.kind in {DomainFieldKind.STRING, DomainFieldKind.TEXT, DomainFieldKind.MEDIA, DomainFieldKind.RELATION, DomainFieldKind.ENUM}:
            if not isinstance(value, str): raise InvalidDomain(f"Domain field has an invalid type: {field.field_id}")
            value = value.strip()
            maximum = field.maximum_length or (100_000 if field.kind is DomainFieldKind.TEXT else 500)
            if not value or len(value) > maximum: raise InvalidDomain(f"Domain field has an invalid length: {field.field_id}")
            if field.kind is DomainFieldKind.ENUM and value not in field.choices: raise InvalidDomain(f"Domain field has an invalid choice: {field.field_id}")
            if field.kind in {DomainFieldKind.MEDIA, DomainFieldKind.RELATION}:
                try: value = str(UUID(value))
                except (ValueError, TypeError) as exc: raise InvalidDomain(f"Domain field has an invalid reference: {field.field_id}") from exc
        elif field.kind is DomainFieldKind.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool): raise InvalidDomain(f"Domain field has an invalid type: {field.field_id}")
        elif field.kind is DomainFieldKind.DECIMAL:
            try: value = format(Decimal(str(value)), "f")
            except (InvalidOperation, ValueError) as exc: raise InvalidDomain(f"Domain field has an invalid decimal: {field.field_id}") from exc
        elif field.kind is DomainFieldKind.BOOLEAN:
            if not isinstance(value, bool): raise InvalidDomain(f"Domain field has an invalid type: {field.field_id}")
        output[field.field_id] = value
    return MappingProxyType(output)


def _identifier(value: object) -> bool: return isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_.-]{2,127}", value) is not None
def _dump(value: Mapping[str, object]) -> str: return json.dumps(dict(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _record_values(record: DomainRecord) -> dict[str, str]: return {"record_id": record.record_id, "entity_type": record.entity_type, "owner": record.owner, "record_values": _dump(record.values), "owner_user_id": record.owner_user_id, "created_at": record.created_at, "updated_at": record.updated_at}
def _from_row(row: Mapping[str, object]) -> DomainRecord:
    try: values = json.loads(str(row["record_values"]))
    except (json.JSONDecodeError, TypeError) as exc: raise DomainError("Stored domain record is invalid") from exc
    if not isinstance(values, dict): raise DomainError("Stored domain record is invalid")
    return DomainRecord(str(row["record_id"]), str(row["entity_type"]), str(row["owner"]), MappingProxyType(values), str(row["owner_user_id"]), str(row["created_at"]), str(row["updated_at"]))
