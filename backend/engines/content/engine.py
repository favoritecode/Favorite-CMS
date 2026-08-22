"""Generic contract-driven Content Resource lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from sqlalchemy import Column, MetaData, String, Table, Text, delete, insert, select, update

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.authentication import AuthenticationContext
from backend.engines.cache import CacheEngine, CacheScope
from backend.engines.data_contracts import dump_mapping, identifier, json_mapping, load_mapping, text
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.permissions import AuthorizationContext, PermissionEngine


class ContentError(ApplicationFailure): pass
class InvalidContent(ValidationFailure): pass


class ContentState(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentVisibility(StrEnum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class FieldKind(StrEnum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass(frozen=True)
class ContentField:
    name: str
    kind: FieldKind
    required: bool = False

    def __post_init__(self) -> None:
        identifier(self.name, "Content field")


@dataclass(frozen=True)
class ContentType:
    type_id: str
    owner: str
    display_name: str
    fields: tuple[ContentField, ...]
    permissions: Mapping[str, str]
    publishable: bool = True
    archivable: bool = True

    def __post_init__(self) -> None:
        identifier(self.type_id, "Content Type")
        identifier(self.owner, "Content Type owner")
        text(self.display_name, "Content Type display name", maximum=255)
        if len({item.name for item in self.fields}) != len(self.fields):
            raise InvalidContent("Content Type fields conflict")
        required = {"create", "read", "update", "delete", "publish", "archive"}
        if set(self.permissions) != required or any(not value.strip() for value in self.permissions.values()):
            raise InvalidContent("Content Type permissions are incomplete")
        object.__setattr__(self, "permissions", MappingProxyType(dict(self.permissions)))


@dataclass(frozen=True)
class ContentResource:
    content_id: str
    type_id: str
    title: str
    data: Mapping[str, object]
    metadata: Mapping[str, object]
    state: ContentState
    owner_user_id: str
    created_at: str
    updated_at: str
    published_at: str | None


@dataclass(frozen=True)
class ContentQuery:
    type_id: str | None = None
    state: ContentState | None = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class ContentSeoMetadata:
    """Content-owned, presentation-safe SEO fields available to approved consumers."""
    title: str = ""
    description: str = ""
    canonical_path: str = ""
    robots: str = "index,follow"
    open_graph_title: str = ""
    open_graph_description: str = ""
    open_graph_image: str = ""


@dataclass(frozen=True)
class ContentSeoProjection:
    content_id: str
    title: str
    description: str
    canonical: str
    robots: str
    open_graph_title: str
    open_graph_description: str
    open_graph_image: str


_metadata = MetaData()
_content = Table(
    "favorite_content_resources", _metadata,
    Column("content_id", String(36), primary_key=True),
    Column("type_id", String(255), nullable=False), Column("title", String(500), nullable=False),
    Column("data", Text, nullable=False), Column("metadata", Text, nullable=False),
    Column("state", String(32), nullable=False), Column("owner_user_id", String(36), nullable=False),
    Column("created_at", String(64), nullable=False), Column("updated_at", String(64), nullable=False),
    Column("published_at", String(64), nullable=True),
)


def content_migration() -> Migration:
    return Migration("platform.content.001", "engine.content",
                     lambda connection: _metadata.create_all(connection, tables=[_content]),
                     dependencies=("platform.user.001",))


class ContentEngine:
    engine_id = "content"
    dependencies = ("database", "migrations", "permissions", "cache")

    def __init__(self) -> None:
        self._types: dict[str, ContentType] = {}
        self._database: DatabaseEngine | None = None
        self._permissions: PermissionEngine | None = None
        self._cache: CacheEngine | None = None
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        self._cache = container.resolve("engine.cache", CacheEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(content_migration())
        container.register("engine.content", self)

    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False

    def register_type(self, contract: ContentType) -> None:
        if contract.type_id in self._types:
            raise InvalidContent("Content Type is already registered")
        self._types[contract.type_id] = contract

    def create(self, type_id: str, *, title: str, data: Mapping[str, object],
               metadata: Mapping[str, object], authentication: AuthenticationContext) -> ContentResource:
        contract = self._type(type_id)
        owner = authentication.user_id or ""
        self._authorize(contract, "create", authentication, owner_user_id=owner)
        valid_data = self._validate_data(contract, data)
        now = _now()
        resource = ContentResource(str(uuid4()), contract.type_id, text(title, "Content title", maximum=500),
                                   valid_data, json_mapping(metadata, "Content metadata"), ContentState.DRAFT,
                                   owner, now, now, None)
        with self._db().transaction() as session:
            session.execute(insert(_content).values(**_values(resource)))
        self._invalidate()
        return resource

    def get(self, content_id: str, authentication: AuthenticationContext | None = None) -> ContentResource:
        resource = self._load(content_id)
        self._authorize(self._type(resource.type_id), "read", authentication,
                        resource_id=resource.content_id, owner_user_id=resource.owner_user_id,
                        public=_direct_public(resource))
        return resource

    def query(self, query: ContentQuery, authentication: AuthenticationContext | None = None) -> tuple[ContentResource, ...]:
        if query.page < 1 or not 1 <= query.page_size <= 100:
            raise InvalidContent("Content pagination is invalid")
        statement = select(_content)
        if query.type_id is not None:
            self._type(query.type_id); statement = statement.where(_content.c.type_id == query.type_id)
        if query.state is not None: statement = statement.where(_content.c.state == query.state.value)
        statement = statement.order_by(_content.c.content_id).offset((query.page - 1) * query.page_size).limit(query.page_size)
        with self._db().session() as session:
            resources = tuple(_from_row(row) for row in session.execute(statement).mappings())
        visible: list[ContentResource] = []
        for resource in resources:
            if authentication is None and not _listed_public(resource):
                continue
            decision = self._permissions_required().evaluate(
                self._type(resource.type_id).permissions["read"],
                AuthorizationContext("read", "content", authentication, resource.content_id,
                                     resource.owner_user_id, _listed_public(resource)),
            )
            if decision.allowed: visible.append(resource)
        return tuple(visible)

    def update(self, content_id: str, *, title: str, data: Mapping[str, object],
               metadata: Mapping[str, object], authentication: AuthenticationContext) -> ContentResource:
        current = self._load(content_id); contract = self._type(current.type_id)
        self._authorize(contract, "update", authentication, resource_id=current.content_id,
                        owner_user_id=current.owner_user_id)
        values = {"title": text(title, "Content title", maximum=500),
                  "data": dump_mapping(self._validate_data(contract, data)),
                  "metadata": dump_mapping(json_mapping(metadata, "Content metadata")), "updated_at": _now()}
        with self._db().transaction() as session:
            session.execute(update(_content).where(_content.c.content_id == current.content_id).values(**values))
        self._invalidate(); return self._load(current.content_id)

    def set_seo_metadata(self, content_id: str, metadata: ContentSeoMetadata,
                         authentication: AuthenticationContext) -> ContentResource:
        """Update the Content-owned SEO namespace through Content authorization."""
        current = self._load(content_id); contract = self._type(current.type_id)
        self._authorize(contract, "update", authentication, resource_id=current.content_id,
                        owner_user_id=current.owner_user_id)
        safe = _seo_values(metadata)
        values = dict(current.metadata)
        if any(safe.values()): values["seo"] = safe
        else: values.pop("seo", None)
        with self._db().transaction() as session:
            session.execute(update(_content).where(_content.c.content_id == current.content_id)
                            .values(metadata=dump_mapping(values), updated_at=_now()))
        self._invalidate(); return self._load(current.content_id)

    def get_seo_metadata(self, content_id: str,
                         authentication: AuthenticationContext) -> ContentSeoMetadata:
        current = self._load(content_id); contract = self._type(current.type_id)
        self._authorize(contract, "read", authentication, resource_id=current.content_id,
                        owner_user_id=current.owner_user_id,
                        public=_direct_public(current))
        return _seo_metadata(current.metadata.get("seo", {}))

    def seo_projection(self, content_id: str, *, public_origin: str) -> ContentSeoProjection | None:
        """Project published Content without exposing persistence or draft/private data."""
        current = self._load(content_id)
        if not _direct_public(current):
            return None
        origin = _public_origin(public_origin)
        raw = current.metadata.get("seo", {})
        metadata = _seo_metadata(raw)
        body = current.data.get("body", "")
        default_description = str(body).strip()[:320] if isinstance(body, str) else ""
        path = metadata.canonical_path or f"/site/content/{current.content_id}"
        canonical = origin + path
        image = origin + metadata.open_graph_image if metadata.open_graph_image else ""
        description = metadata.description or default_description
        return ContentSeoProjection(
            current.content_id, metadata.title or current.title, description, canonical, metadata.robots,
            metadata.open_graph_title or current.title,
            metadata.open_graph_description or description, image,
        )

    def publish(self, content_id: str, authentication: AuthenticationContext) -> ContentResource:
        return self._transition(content_id, ContentState.DRAFT, ContentState.PUBLISHED, "publish", authentication)

    def archive(self, content_id: str, authentication: AuthenticationContext) -> ContentResource:
        return self._transition(content_id, ContentState.PUBLISHED, ContentState.ARCHIVED, "archive", authentication)

    def unpublish(self, content_id: str, authentication: AuthenticationContext) -> ContentResource:
        """Return published Content to a draft through the existing publish permission."""
        return self._transition(content_id, ContentState.PUBLISHED, ContentState.DRAFT, "publish", authentication)

    def delete(self, content_id: str, authentication: AuthenticationContext) -> None:
        current = self._load(content_id); contract = self._type(current.type_id)
        self._authorize(contract, "delete", authentication, resource_id=current.content_id,
                        owner_user_id=current.owner_user_id)
        with self._db().transaction() as session:
            session.execute(delete(_content).where(_content.c.content_id == current.content_id))
        self._invalidate()

    def _transition(self, content_id: str, source: ContentState, target: ContentState, action: str,
                    authentication: AuthenticationContext) -> ContentResource:
        current = self._load(content_id); contract = self._type(current.type_id)
        if current.state is not source or (action == "publish" and not contract.publishable) or (action == "archive" and not contract.archivable):
            raise InvalidContent("Content lifecycle transition is invalid")
        self._validate_data(contract, current.data)
        self._authorize(contract, action, authentication, resource_id=current.content_id,
                        owner_user_id=current.owner_user_id)
        now = _now(); values: dict[str, str | None] = {"state": target.value, "updated_at": now}
        if target is ContentState.PUBLISHED: values["published_at"] = now
        elif target is ContentState.DRAFT: values["published_at"] = None
        with self._db().transaction() as session:
            session.execute(update(_content).where(_content.c.content_id == current.content_id).values(**values))
        self._invalidate(); return self._load(current.content_id)

    def _validate_data(self, contract: ContentType, data: Mapping[str, object]) -> Mapping[str, object]:
        result = json_mapping(data, "Content data")
        fields = {field.name: field for field in contract.fields}
        if set(result) - set(fields): raise InvalidContent("Content data contains unsupported fields")
        for field in contract.fields:
            if field.required and field.name not in result: raise InvalidContent("Content data is incomplete")
            if field.name in result and not _kind_matches(field.kind, result[field.name]):
                raise InvalidContent("Content field type is invalid")
        return result

    def _authorize(self, contract: ContentType, action: str, authentication: AuthenticationContext | None,
                   *, resource_id: str | None = None, owner_user_id: str | None = None,
                   public: bool = False) -> None:
        self._permissions_required().require(contract.permissions[action], AuthorizationContext(
            action, "content", authentication, resource_id, owner_user_id, public))

    def _load(self, value: str) -> ContentResource:
        try: content_id = str(UUID(value))
        except (ValueError, TypeError) as exc: raise InvalidContent("Content identifier is invalid") from exc
        with self._db().session() as session:
            row = session.execute(select(_content).where(_content.c.content_id == content_id)).mappings().first()
        if row is None: raise ContentError("Content Resource was not found")
        return _from_row(row)

    def _type(self, type_id: str) -> ContentType:
        try: return self._types[type_id]
        except KeyError as exc: raise InvalidContent("Content Type is not registered") from exc

    def _db(self) -> DatabaseEngine:
        if not self.ready or self._database is None: raise ContentError("Content Engine is unavailable")
        return self._database
    def _permissions_required(self) -> PermissionEngine:
        if self._permissions is None: raise ContentError("Permission service is unavailable")
        return self._permissions
    def _invalidate(self) -> None:
        if self._cache is not None: self._cache.clear(CacheScope("resources", "engine.content"))


def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _kind_matches(kind: FieldKind, value: object) -> bool:
    return {FieldKind.STRING: lambda: isinstance(value, str), FieldKind.NUMBER: lambda: isinstance(value, (int, float)) and not isinstance(value, bool),
            FieldKind.BOOLEAN: lambda: isinstance(value, bool), FieldKind.OBJECT: lambda: isinstance(value, dict),
            FieldKind.ARRAY: lambda: isinstance(value, list)}[kind]()
def _values(item: ContentResource) -> dict[str, object]:
    return {"content_id": item.content_id, "type_id": item.type_id, "title": item.title,
            "data": dump_mapping(item.data), "metadata": dump_mapping(item.metadata), "state": item.state.value,
            "owner_user_id": item.owner_user_id, "created_at": item.created_at, "updated_at": item.updated_at,
            "published_at": item.published_at}
def _from_row(row: Mapping[str, object]) -> ContentResource:
    return ContentResource(str(row["content_id"]), str(row["type_id"]), str(row["title"]),
                           load_mapping(str(row["data"])), load_mapping(str(row["metadata"])),
                           ContentState(str(row["state"])), str(row["owner_user_id"]),
                           str(row["created_at"]), str(row["updated_at"]),
                           None if row["published_at"] is None else str(row["published_at"]))


def content_visibility(item: ContentResource) -> ContentVisibility:
    raw = item.data.get("visibility", ContentVisibility.PUBLIC.value)
    try: return ContentVisibility(str(raw))
    except ValueError: return ContentVisibility.PRIVATE


def _listed_public(item: ContentResource) -> bool:
    return item.state is ContentState.PUBLISHED and content_visibility(item) is ContentVisibility.PUBLIC


def _direct_public(item: ContentResource) -> bool:
    return item.state is ContentState.PUBLISHED and content_visibility(item) in {ContentVisibility.PUBLIC, ContentVisibility.UNLISTED}


def _public_origin(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
        raise InvalidContent("Public SEO origin is invalid")
    return value.rstrip("/")


def _seo_metadata(value: object) -> ContentSeoMetadata:
    if value in ({}, None): return ContentSeoMetadata()
    if not isinstance(value, Mapping): raise InvalidContent("Content SEO metadata is invalid")
    expected = {"title", "description", "canonical_path", "robots", "open_graph_title",
                "open_graph_description", "open_graph_image"}
    legacy = expected - {"title"}
    if frozenset(value) not in {frozenset(expected), frozenset(legacy)} or any(not isinstance(value[key], str) for key in value):
        raise InvalidContent("Content SEO metadata is invalid")
    return ContentSeoMetadata(**{key: str(value.get(key, "")) for key in expected})


def _seo_values(value: ContentSeoMetadata) -> dict[str, str]:
    if not isinstance(value, ContentSeoMetadata): raise InvalidContent("Content SEO metadata is invalid")
    result = {
        "title": _optional_text(value.title, "SEO title", 120),
        "description": _optional_text(value.description, "SEO description", 320),
        "canonical_path": _optional_text(value.canonical_path, "SEO canonical path", 500),
        "robots": value.robots,
        "open_graph_title": _optional_text(value.open_graph_title, "Open Graph title", 200),
        "open_graph_description": _optional_text(value.open_graph_description, "Open Graph description", 320),
        "open_graph_image": _optional_text(value.open_graph_image, "Open Graph image", 500),
    }
    if result["robots"] not in {"index,follow", "noindex,nofollow"}:
        raise InvalidContent("Content SEO robots metadata is invalid")
    for key in ("canonical_path", "open_graph_image"):
        path = result[key]
        if path and (not path.startswith("/") or path.startswith("//") or "\\" in path or ".." in path.split("/")):
            raise InvalidContent("Content SEO path metadata is invalid")
    return result


def _optional_text(value: str, label: str, maximum: int) -> str:
    if not isinstance(value, str): raise InvalidContent(f"{label} is invalid")
    normalized = value.strip()
    if len(normalized) > maximum: raise InvalidContent(f"{label} is invalid")
    return normalized
