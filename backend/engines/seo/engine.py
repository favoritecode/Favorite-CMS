"""Deterministic SEO metadata coordination without Routing or Rendering ownership."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import json
from typing import Callable, Mapping
from urllib.parse import urlsplit

from sqlalchemy import Column, MetaData, String, Table, Text, delete, insert, select

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.data_contracts import dump_mapping, identifier, json_mapping, load_mapping
from backend.engines.errors import ApplicationFailure, ValidationFailure


class SeoError(ApplicationFailure): pass
class InvalidSeo(ValidationFailure): pass


class SeoSource(IntEnum):
    PLATFORM_DEFAULT = 10
    PLUGIN = 20
    RESOURCE = 30
    EXPLICIT = 40


@dataclass(frozen=True)
class SeoResourceContext:
    resource_type: str
    resource_id: str
    def __post_init__(self) -> None:
        identifier(self.resource_type, "SEO Resource Type")
        if not self.resource_id.strip(): raise InvalidSeo("SEO Resource identifier is invalid")


@dataclass(frozen=True)
class SeoMetadata:
    title: str | None = None
    description: str | None = None
    canonical: str | None = None
    social: Mapping[str, object] | None = None
    structured: Mapping[str, object] | None = None


@dataclass(frozen=True)
class SeoContribution:
    context: SeoResourceContext
    owner: str
    source: SeoSource
    metadata: SeoMetadata
    def __post_init__(self) -> None:
        identifier(self.owner, "SEO owner"); _validate_metadata(self.metadata)


_metadata = MetaData()
_seo = Table("favorite_seo_metadata", _metadata,
             Column("resource_type", String(255), primary_key=True), Column("resource_id", String(255), primary_key=True),
             Column("owner", String(255), primary_key=True), Column("source", String(32), primary_key=True),
             Column("metadata", Text, nullable=False))


def seo_migration() -> Migration:
    return Migration("platform.seo.001", "engine.seo",
                     lambda connection: _metadata.create_all(connection, tables=[_seo]))


class SeoEngine:
    engine_id = "seo"
    dependencies = ("database", "migrations")
    def __init__(self) -> None:
        self._database: DatabaseEngine | None = None
        self._visibility: dict[str, tuple[str, Callable[[str], bool]]] = {}
        self.ready = False
    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(seo_migration())
        container.register("engine.seo", self)
    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False
    def register_resource_type(self, resource_type: str, *, owner: str,
                               is_public: Callable[[str], bool]) -> None:
        resource_type = identifier(resource_type, "SEO Resource Type"); owner = identifier(owner, "SEO Resource owner")
        if resource_type in self._visibility or not callable(is_public):
            raise InvalidSeo("SEO Resource Type is already registered")
        self._visibility[resource_type] = (owner, is_public)
    def set(self, contribution: SeoContribution) -> None:
        registered = self._visibility.get(contribution.context.resource_type)
        if registered is None or (contribution.source in {SeoSource.RESOURCE, SeoSource.PLUGIN} and contribution.owner != registered[0]):
            raise InvalidSeo("SEO contribution owner is not approved")
        values = _values(contribution)
        with self._db().transaction() as session:
            session.execute(delete(_seo).where((_seo.c.resource_type == contribution.context.resource_type) &
                                               (_seo.c.resource_id == contribution.context.resource_id) &
                                               (_seo.c.owner == contribution.owner) &
                                               (_seo.c.source == str(int(contribution.source)))))
            session.execute(insert(_seo).values(**values))
    def remove(self, context: SeoResourceContext, *, owner: str, source: SeoSource) -> None:
        with self._db().transaction() as session:
            session.execute(delete(_seo).where((_seo.c.resource_type == context.resource_type) &
                                               (_seo.c.resource_id == context.resource_id) &
                                               (_seo.c.owner == owner) & (_seo.c.source == str(int(source)))))
    def resolve(self, context: SeoResourceContext) -> SeoMetadata:
        registered = self._visibility.get(context.resource_type)
        if registered is None: raise InvalidSeo("SEO Resource Type is not registered")
        try:
            if not registered[1](context.resource_id): return SeoMetadata()
        except Exception:
            return SeoMetadata()
        with self._db().session() as session:
            rows = tuple(session.execute(select(_seo).where((_seo.c.resource_type == context.resource_type) &
                                                            (_seo.c.resource_id == context.resource_id))).mappings())
        contributions = sorted(rows, key=lambda row: (-int(str(row["source"])), str(row["owner"])))
        fields: dict[str, object] = {}
        for row in contributions:
            values = load_mapping(str(row["metadata"]))
            for key, value in values.items():
                if key not in fields and value is not None: fields[key] = value
        metadata = SeoMetadata(fields.get("title"), fields.get("description"), fields.get("canonical"),
                               fields.get("social"), fields.get("structured"))
        _validate_metadata(metadata); return metadata
    def _db(self) -> DatabaseEngine:
        if not self.ready or self._database is None: raise SeoError("SEO Engine is unavailable")
        return self._database


def _validate_metadata(value: SeoMetadata) -> None:
    if value.title is not None and (not value.title.strip() or len(value.title) > 500): raise InvalidSeo("SEO title is invalid")
    if value.description is not None and (not value.description.strip() or len(value.description) > 2000): raise InvalidSeo("SEO description is invalid")
    if value.canonical is not None:
        parsed = urlsplit(value.canonical)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise InvalidSeo("Canonical Reference is invalid")
    if value.social is not None: json_mapping(value.social, "Social metadata")
    if value.structured is not None: json_mapping(value.structured, "Structured metadata")
def _values(item: SeoContribution) -> dict[str, str]:
    payload = {"title": item.metadata.title, "description": item.metadata.description,
               "canonical": item.metadata.canonical, "social": item.metadata.social,
               "structured": item.metadata.structured}
    return {"resource_type": item.context.resource_type, "resource_id": item.context.resource_id,
            "owner": item.owner, "source": str(int(item.source)), "metadata": dump_mapping(payload)}
