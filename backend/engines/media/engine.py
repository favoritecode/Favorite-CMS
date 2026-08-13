"""Media Resource lifecycle coordinated through the platform Storage Engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import PurePath
import re
from types import MappingProxyType
from typing import Callable, Mapping
from uuid import UUID, uuid4

from sqlalchemy import Column, MetaData, String, Table, Text, delete, insert, select, update

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.authentication import AuthenticationContext
from backend.engines.data_contracts import dump_mapping, json_mapping, load_mapping, text
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.permissions import AuthorizationContext, PermissionDenied, PermissionEngine
from backend.engines.storage import StorageEngine, StorageError, StorageReference, StorageScope


class MediaError(ApplicationFailure): pass
class InvalidMedia(ValidationFailure): pass


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


@dataclass(frozen=True)
class MediaAccessContract:
    owner: str
    permissions: Mapping[str, str]

    def __post_init__(self) -> None:
        required = {"create", "read", "update", "delete"}
        if not self.owner.strip() or set(self.permissions) != required:
            raise InvalidMedia("Media access contract is invalid")
        object.__setattr__(self, "permissions", MappingProxyType(dict(self.permissions)))


@dataclass(frozen=True)
class MediaResource:
    media_id: str
    media_type: MediaType
    file_name: str
    mime_type: str
    size: int
    metadata: Mapping[str, object]
    owner_user_id: str
    public: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class MediaDelivery:
    media_id: str
    reference: str
    mime_type: str
    size: int


MediaProcessor = Callable[[bytes, Mapping[str, object]], bytes]


_metadata = MetaData()
_media = Table(
    "favorite_media_resources", _metadata,
    Column("media_id", String(36), primary_key=True), Column("media_type", String(32), nullable=False),
    Column("file_name", String(255), nullable=False), Column("mime_type", String(255), nullable=False),
    Column("size", String(32), nullable=False), Column("metadata", Text, nullable=False),
    Column("owner_user_id", String(36), nullable=False), Column("is_public", String(5), nullable=False),
    Column("storage_identifier", String(512), nullable=False), Column("storage_provider", String(64), nullable=False),
    Column("created_at", String(64), nullable=False), Column("updated_at", String(64), nullable=False),
)
_scope = StorageScope("resources", "engine.media")
_filename = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,254}$")
_mime = re.compile(r"^[a-z0-9][a-z0-9.+-]*/[a-z0-9][a-z0-9.+-]*$")


def media_migration() -> Migration:
    return Migration("platform.media.001", "engine.media",
                     lambda connection: _metadata.create_all(connection, tables=[_media]),
                     dependencies=("platform.user.001",))


class MediaEngine:
    engine_id = "media"
    dependencies = ("database", "migrations", "storage", "permissions")

    def __init__(self) -> None:
        self._access: MediaAccessContract | None = None
        self._database: DatabaseEngine | None = None
        self._storage: StorageEngine | None = None
        self._permissions: PermissionEngine | None = None
        self._processors: dict[str, MediaProcessor] = {}
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        self._storage = container.resolve("engine.storage", StorageEngine)
        self._permissions = container.resolve("engine.permissions", PermissionEngine)
        container.resolve("engine.migrations", DatabaseMigrationEngine).register(media_migration())
        container.register("engine.media", self)

    def start(self) -> None: self.ready = True
    def shutdown(self) -> None: self.ready = False

    def register_access(self, contract: MediaAccessContract) -> None:
        if self._access is not None: raise InvalidMedia("Media access contract is already registered")
        self._access = contract

    def register_processor(self, processor_id: str, processor: MediaProcessor) -> None:
        from backend.engines.data_contracts import identifier
        processor_id = identifier(processor_id, "Media processor")
        if processor_id in self._processors or not callable(processor):
            raise InvalidMedia("Media processor is invalid")
        self._processors[processor_id] = processor

    def upload(self, *, media_type: MediaType, file_name: str, mime_type: str, data: bytes,
               metadata: Mapping[str, object], public: bool,
               authentication: AuthenticationContext) -> MediaResource:
        if not isinstance(media_type, MediaType) or not isinstance(data, bytes) or not data:
            raise InvalidMedia("Media input is invalid")
        name = file_name.strip()
        if PurePath(name).name != name or not _filename.fullmatch(name) or not _mime.fullmatch(mime_type):
            raise InvalidMedia("Media file information is invalid")
        owner = authentication.user_id or ""
        self._authorize("create", authentication, owner_user_id=owner)
        media_id = str(uuid4()); storage_identifier = f"{media_id}/{name.replace(' ', '_')}"
        reference = self._storage_required().store(_scope, storage_identifier, data)
        now = _now()
        resource = MediaResource(media_id, media_type, name, mime_type, len(data),
                                 json_mapping(metadata, "Media metadata"), owner, bool(public), now, now)
        try:
            with self._db().transaction() as session:
                session.execute(insert(_media).values(**_values(resource, reference)))
        except Exception:
            try: self._storage_required().delete(reference, scope=_scope)
            except StorageError: pass
            raise
        return resource

    def get(self, media_id: str, authentication: AuthenticationContext | None = None) -> MediaResource:
        resource, _ = self._load(media_id)
        self._authorize("read", authentication, resource_id=resource.media_id,
                        owner_user_id=resource.owner_user_id, public=resource.public)
        return resource

    def list(self, authentication: AuthenticationContext | None = None) -> tuple[MediaResource, ...]:
        """Return visible Media Resources in deterministic identity order."""
        with self._db().session() as session:
            rows = session.execute(select(_media).order_by(_media.c.media_id)).mappings()
            resources = tuple(_resource_from_row(row) for row in rows)
        visible: list[MediaResource] = []
        for resource in resources:
            try:
                self._authorize("read", authentication, resource_id=resource.media_id,
                                owner_user_id=resource.owner_user_id, public=resource.public)
            except PermissionDenied:
                continue
            visible.append(resource)
        return tuple(visible)

    def retrieve(self, media_id: str, authentication: AuthenticationContext | None = None) -> bytes:
        resource, reference = self._load(media_id)
        self._authorize("read", authentication, resource_id=resource.media_id,
                        owner_user_id=resource.owner_user_id, public=resource.public)
        return self._storage_required().retrieve(reference, scope=_scope)

    def update_metadata(self, media_id: str, metadata: Mapping[str, object],
                        authentication: AuthenticationContext) -> MediaResource:
        resource, _ = self._load(media_id)
        self._authorize("update", authentication, resource_id=resource.media_id,
                        owner_user_id=resource.owner_user_id)
        valid = json_mapping(metadata, "Media metadata")
        with self._db().transaction() as session:
            session.execute(update(_media).where(_media.c.media_id == resource.media_id)
                            .values(metadata=dump_mapping(valid), updated_at=_now()))
        return self._load(resource.media_id)[0]

    def process(self, media_id: str, processor_id: str, options: Mapping[str, object],
                authentication: AuthenticationContext) -> bytes:
        resource, reference = self._load(media_id)
        self._authorize("update", authentication, resource_id=resource.media_id,
                        owner_user_id=resource.owner_user_id)
        try: processor = self._processors[processor_id]
        except KeyError as exc: raise InvalidMedia("Media processor is not registered") from exc
        original = self._storage_required().retrieve(reference, scope=_scope)
        try: result = processor(original, json_mapping(options, "Media processing options"))
        except Exception as exc: raise MediaError("Media processing failed") from exc
        if not isinstance(result, bytes) or not result: raise MediaError("Media processing failed")
        return result

    def delivery(self, media_id: str, authentication: AuthenticationContext | None = None) -> MediaDelivery:
        resource = self.get(media_id, authentication)
        return MediaDelivery(resource.media_id, f"media:{resource.media_id}", resource.mime_type, resource.size)

    def delete(self, media_id: str, authentication: AuthenticationContext) -> None:
        resource, reference = self._load(media_id)
        self._authorize("delete", authentication, resource_id=resource.media_id,
                        owner_user_id=resource.owner_user_id)
        original = self._storage_required().retrieve(reference, scope=_scope)
        self._storage_required().delete(reference, scope=_scope)
        try:
            with self._db().transaction() as session:
                session.execute(delete(_media).where(_media.c.media_id == resource.media_id))
        except Exception:
            try: self._storage_required().store(_scope, reference.identifier, original)
            except StorageError: pass
            raise

    def _load(self, value: str) -> tuple[MediaResource, StorageReference]:
        try: media_id = str(UUID(value))
        except (ValueError, TypeError) as exc: raise InvalidMedia("Media identifier is invalid") from exc
        with self._db().session() as session:
            row = session.execute(select(_media).where(_media.c.media_id == media_id)).mappings().first()
        if row is None: raise MediaError("Media Resource was not found")
        resource = _resource_from_row(row)
        return resource, StorageReference(str(row["storage_identifier"]), _scope, str(row["storage_provider"]))

    def _authorize(self, action: str, authentication: AuthenticationContext | None, **context: object) -> None:
        if self._access is None: raise MediaError("Media access contract is unavailable")
        self._permissions_required().require(self._access.permissions[action], AuthorizationContext(
            action, "media", authentication, context.get("resource_id"), context.get("owner_user_id"),
            bool(context.get("public", False))))
    def _db(self) -> DatabaseEngine:
        if not self.ready or self._database is None: raise MediaError("Media Engine is unavailable")
        return self._database
    def _storage_required(self) -> StorageEngine:
        if self._storage is None: raise MediaError("Storage service is unavailable")
        return self._storage
    def _permissions_required(self) -> PermissionEngine:
        if self._permissions is None: raise MediaError("Permission service is unavailable")
        return self._permissions


def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _resource_from_row(row: Mapping[str, object]) -> MediaResource:
    return MediaResource(str(row["media_id"]), MediaType(str(row["media_type"])),
                         str(row["file_name"]), str(row["mime_type"]), int(str(row["size"])),
                         load_mapping(str(row["metadata"])), str(row["owner_user_id"]),
                         str(row["is_public"]) == "true", str(row["created_at"]), str(row["updated_at"]))
def _values(item: MediaResource, reference: StorageReference) -> dict[str, object]:
    return {"media_id": item.media_id, "media_type": item.media_type.value, "file_name": item.file_name,
            "mime_type": item.mime_type, "size": str(item.size), "metadata": dump_mapping(item.metadata),
            "owner_user_id": item.owner_user_id, "is_public": str(item.public).lower(),
            "storage_identifier": reference.identifier, "storage_provider": reference.provider,
            "created_at": item.created_at, "updated_at": item.updated_at}
