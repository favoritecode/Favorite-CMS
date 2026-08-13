"""Scoped provider-neutral physical storage infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import re
import shutil
from typing import Callable, Protocol, TypeVar

from backend.config import Configuration, SecretValue
from backend.core.container import ServiceContainer


class StorageError(RuntimeError):
    pass


T = TypeVar("T")


_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class StorageScope:
    name: str
    owner: str

    def __post_init__(self) -> None:
        _validate_segment(self.name, "scope")
        _validate_segment(self.owner, "owner")

    @property
    def key(self) -> str:
        return f"{self.owner}/{self.name}"


@dataclass(frozen=True)
class StorageReference:
    identifier: str
    scope: StorageScope
    provider: str

    def __post_init__(self) -> None:
        _validate_identifier(self.identifier)


@dataclass(frozen=True)
class StorageMetadata:
    reference: StorageReference
    size: int
    created_at: str
    updated_at: str


class StorageProvider(Protocol):
    name: str
    def store(self, scope: StorageScope, identifier: str, data: bytes, *, overwrite: bool) -> None: ...
    def retrieve(self, scope: StorageScope, identifier: str) -> bytes: ...
    def delete(self, scope: StorageScope, identifier: str) -> None: ...
    def exists(self, scope: StorageScope, identifier: str) -> bool: ...
    def copy(self, source: StorageReference, destination: StorageReference, *, overwrite: bool) -> None: ...
    def move(self, source: StorageReference, destination: StorageReference, *, overwrite: bool) -> None: ...
    def metadata(self, reference: StorageReference) -> StorageMetadata: ...
    def healthcheck(self) -> bool: ...
    def list(self, scope: StorageScope) -> tuple[str, ...]: ...


class LocalStorageProvider:
    name = "local"

    def __init__(self, root: Path) -> None:
        if not root.is_absolute():
            root = (Path.cwd() / root).resolve()
        self._root = root.resolve()

    def start(self) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        if not self._root.is_dir():
            raise StorageError("Storage Provider is unavailable")

    def store(self, scope: StorageScope, identifier: str, data: bytes, *, overwrite: bool) -> None:
        target = self._path(scope, identifier)
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "wb" if overwrite else "xb"
        try:
            with target.open(mode) as handle:
                handle.write(data)
        except FileExistsError as exc:
            raise StorageError("Storage Resource already exists") from exc
        except OSError as exc:
            raise StorageError("Storage write failed") from exc

    def retrieve(self, scope: StorageScope, identifier: str) -> bytes:
        try:
            return self._path(scope, identifier).read_bytes()
        except FileNotFoundError as exc:
            raise StorageError("Storage Resource was not found") from exc
        except OSError as exc:
            raise StorageError("Storage retrieval failed") from exc

    def delete(self, scope: StorageScope, identifier: str) -> None:
        try:
            self._path(scope, identifier).unlink()
        except FileNotFoundError as exc:
            raise StorageError("Storage Resource was not found") from exc
        except OSError as exc:
            raise StorageError("Storage deletion failed") from exc

    def exists(self, scope: StorageScope, identifier: str) -> bool:
        return self._path(scope, identifier).is_file()

    def copy(self, source: StorageReference, destination: StorageReference, *, overwrite: bool) -> None:
        source_path = self._path(source.scope, source.identifier)
        destination_path = self._path(destination.scope, destination.identifier)
        if not source_path.is_file():
            raise StorageError("Storage Resource was not found")
        if destination_path.exists() and not overwrite:
            raise StorageError("Storage Resource already exists")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(source_path, destination_path)
        except OSError as exc:
            raise StorageError("Storage copy failed") from exc

    def move(self, source: StorageReference, destination: StorageReference, *, overwrite: bool) -> None:
        # Copy first so a destination failure cannot remove a valid source.
        self.copy(source, destination, overwrite=overwrite)
        try:
            self.delete(source.scope, source.identifier)
        except StorageError:
            try:
                self.delete(destination.scope, destination.identifier)
            except StorageError:
                pass
            raise StorageError("Storage move failed")

    def metadata(self, reference: StorageReference) -> StorageMetadata:
        try:
            stat = self._path(reference.scope, reference.identifier).stat()
        except FileNotFoundError as exc:
            raise StorageError("Storage Resource was not found") from exc
        except OSError as exc:
            raise StorageError("Storage metadata is unavailable") from exc
        return StorageMetadata(
            reference=reference,
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat(),
            updated_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        )

    def healthcheck(self) -> bool:
        return self._root.is_dir()

    def list(self, scope: StorageScope) -> tuple[str, ...]:
        root = (self._root / scope.owner / scope.name).resolve()
        if not root.exists(): return ()
        try:
            return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and not path.is_symlink()))
        except OSError as exc: raise StorageError("Storage listing failed") from exc

    def _path(self, scope: StorageScope, identifier: str) -> Path:
        _validate_identifier(identifier)
        candidate = (self._root / scope.owner / scope.name / PurePosixPath(identifier)).resolve()
        approved_root = (self._root / scope.owner / scope.name).resolve()
        if approved_root != candidate and approved_root not in candidate.parents:
            raise StorageError("Storage identifier escapes its scope")
        return candidate


class MountedStorageProvider(LocalStorageProvider):
    """Vendor-neutral adapter for an operator-managed persistent filesystem mount."""
    name = "mounted"


class StorageEngine:
    engine_id = "storage"
    dependencies: tuple[str, ...] = ()

    def __init__(self, provider: StorageProvider | None = None) -> None:
        self._provider = provider
        self._configuration: Configuration | None = None
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._configuration = container.resolve("core.configuration", Configuration)
        container.register("engine.storage", self)

    def start(self) -> None:
        if self._provider is None:
            if self._configuration is None:
                raise StorageError("Storage configuration is unavailable")
            root = self._configuration.get("storage.root", SecretValue).reveal()
            try: provider_name = self._configuration.get("storage.provider", str)
            except Exception: provider_name = "local"
            provider = LocalStorageProvider(Path(root)) if provider_name == "local" else MountedStorageProvider(Path(root))
            provider.start()
            self._provider = provider
        if not self._provider.healthcheck():
            raise StorageError("Storage Provider is unavailable")
        self.ready = True

    def shutdown(self) -> None:
        self.ready = False

    def healthcheck(self) -> bool:
        try: return self.ready and self._provider is not None and self._provider.healthcheck()
        except Exception: return False

    @property
    def provider_name(self) -> str:
        return self._require_provider().name

    def store(self, scope: StorageScope, identifier: str, data: bytes, *, overwrite: bool = False) -> StorageReference:
        if not isinstance(data, bytes):
            raise StorageError("Storage data must be bytes")
        reference = StorageReference(identifier, scope, self._require_provider().name)
        self._call("write", lambda: self._require_provider().store(scope, identifier, data, overwrite=overwrite))
        return reference

    def retrieve(self, reference: StorageReference, *, scope: StorageScope) -> bytes:
        self._authorize_reference(reference, scope)
        return self._call("retrieval", lambda: self._require_provider().retrieve(scope, reference.identifier))

    def exists(self, reference: StorageReference, *, scope: StorageScope) -> bool:
        self._authorize_reference(reference, scope)
        return self._call("existence check", lambda: self._require_provider().exists(scope, reference.identifier))

    def delete(self, reference: StorageReference, *, scope: StorageScope) -> None:
        self._authorize_reference(reference, scope)
        self._call("deletion", lambda: self._require_provider().delete(scope, reference.identifier))

    def copy(self, source: StorageReference, *, source_scope: StorageScope, destination_scope: StorageScope,
             destination_identifier: str, overwrite: bool = False) -> StorageReference:
        self._authorize_reference(source, source_scope)
        destination = StorageReference(destination_identifier, destination_scope, self._require_provider().name)
        self._call("copy", lambda: self._require_provider().copy(source, destination, overwrite=overwrite))
        return destination

    def move(self, source: StorageReference, *, source_scope: StorageScope, destination_scope: StorageScope,
             destination_identifier: str, overwrite: bool = False) -> StorageReference:
        self._authorize_reference(source, source_scope)
        destination = StorageReference(destination_identifier, destination_scope, self._require_provider().name)
        self._call("move", lambda: self._require_provider().move(source, destination, overwrite=overwrite))
        return destination

    def metadata(self, reference: StorageReference, *, scope: StorageScope) -> StorageMetadata:
        self._authorize_reference(reference, scope)
        return self._call("metadata", lambda: self._require_provider().metadata(reference))

    def list(self, scope: StorageScope) -> tuple[StorageReference, ...]:
        provider = self._require_provider()
        return tuple(StorageReference(identifier, scope, provider.name) for identifier in self._call("listing", lambda: provider.list(scope)))

    def _authorize_reference(self, reference: StorageReference, scope: StorageScope) -> None:
        if reference.scope != scope or reference.provider != self._require_provider().name:
            raise StorageError("Storage Scope does not own this Resource")

    def _require_provider(self) -> StorageProvider:
        if self._provider is None or not self.ready:
            raise StorageError("Storage Engine is unavailable")
        return self._provider

    def _call(self, operation: str, callback: Callable[[], T]) -> T:
        try:
            return callback()
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"Storage {operation} failed") from exc


def _validate_segment(value: str, label: str) -> None:
    if not _SEGMENT.fullmatch(value) or value in {".", ".."}:
        raise StorageError(f"Storage {label} is invalid")


def _validate_identifier(identifier: str) -> None:
    if not identifier or "\\" in identifier or PurePosixPath(identifier).is_absolute():
        raise StorageError("Storage identifier is invalid")
    parts = PurePosixPath(identifier).parts
    if not parts or any(not _SEGMENT.fullmatch(part) or part in {".", ".."} for part in parts):
        raise StorageError("Storage identifier is invalid")
