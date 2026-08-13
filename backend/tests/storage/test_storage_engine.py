from pathlib import Path

import pytest

from backend.core.container import ServiceContainer
from backend.engines.storage import (
    LocalStorageProvider,
    StorageEngine,
    StorageError,
    StorageScope,
)


def started_storage(tmp_path: Path) -> StorageEngine:
    provider = LocalStorageProvider(tmp_path)
    provider.start()
    storage = StorageEngine(provider)
    storage.initialize(_configuration_container())
    storage.start()
    return storage


def _configuration_container() -> ServiceContainer:
    from backend.config import ConfigField, Configuration, ConfigurationSchema, MappingSource

    schema = ConfigurationSchema((ConfigField("storage.root", str, required=True, secret=True),))
    configuration = Configuration.resolve(
        schema, (MappingSource("test", {"storage.root": "unused"}, 1),)
    )
    container = ServiceContainer()
    container.register("core.configuration", configuration)
    return container


def test_store_retrieve_exists_metadata_and_delete(tmp_path: Path) -> None:
    storage = started_storage(tmp_path)
    scope = StorageScope("assets", "platform")
    reference = storage.store(scope, "nested/file.txt", b"content")
    assert storage.exists(reference, scope=scope)
    assert storage.retrieve(reference, scope=scope) == b"content"
    assert storage.metadata(reference, scope=scope).size == 7
    storage.delete(reference, scope=scope)
    assert not storage.exists(reference, scope=scope)


def test_duplicate_object_requires_explicit_overwrite(tmp_path: Path) -> None:
    storage = started_storage(tmp_path)
    scope = StorageScope("assets", "platform")
    storage.store(scope, "file.txt", b"first")
    with pytest.raises(StorageError, match="already exists"):
        storage.store(scope, "file.txt", b"second")


@pytest.mark.parametrize("identifier", ["../secret", "/absolute", "folder\\file", "a/../../b"])
def test_invalid_or_traversing_identifier_is_rejected(tmp_path: Path, identifier: str) -> None:
    storage = started_storage(tmp_path)
    with pytest.raises(StorageError, match="identifier"):
        storage.store(StorageScope("assets", "platform"), identifier, b"content")


def test_scope_isolation_prevents_cross_owner_access(tmp_path: Path) -> None:
    storage = started_storage(tmp_path)
    owner_a = StorageScope("private", "plugin-a")
    owner_b = StorageScope("private", "plugin-b")
    reference = storage.store(owner_a, "data.bin", b"private")
    with pytest.raises(StorageError, match="does not own"):
        storage.retrieve(reference, scope=owner_b)
    with pytest.raises(StorageError, match="does not own"):
        storage.delete(reference, scope=owner_b)
    assert storage.retrieve(reference, scope=owner_a) == b"private"


def test_copy_and_move_preserve_normalized_references(tmp_path: Path) -> None:
    storage = started_storage(tmp_path)
    source_scope = StorageScope("source", "platform")
    destination_scope = StorageScope("destination", "platform")
    source = storage.store(source_scope, "one.txt", b"one")
    copied = storage.copy(
        source,
        source_scope=source_scope,
        destination_scope=destination_scope,
        destination_identifier="copy.txt",
    )
    assert storage.retrieve(source, scope=source_scope) == b"one"
    assert storage.retrieve(copied, scope=destination_scope) == b"one"
    moved = storage.move(
        source,
        source_scope=source_scope,
        destination_scope=destination_scope,
        destination_identifier="moved.txt",
    )
    assert not storage.exists(source, scope=source_scope)
    assert storage.retrieve(moved, scope=destination_scope) == b"one"


def test_missing_object_is_controlled(tmp_path: Path) -> None:
    storage = started_storage(tmp_path)
    scope = StorageScope("assets", "platform")
    reference = storage.store(scope, "missing.txt", b"content")
    storage.delete(reference, scope=scope)
    with pytest.raises(StorageError, match="not found"):
        storage.retrieve(reference, scope=scope)


def test_provider_failure_is_normalized() -> None:
    class BrokenProvider:
        name = "broken"
        def healthcheck(self) -> bool: return True
        def store(self, *args: object, **kwargs: object) -> None: raise OSError("private path")

    storage = StorageEngine(BrokenProvider())  # type: ignore[arg-type]
    storage.initialize(_configuration_container())
    storage.start()
    with pytest.raises(StorageError, match="write failed") as error:
        storage.store(StorageScope("assets", "platform"), "file.txt", b"content")
    assert "private path" not in str(error.value)

