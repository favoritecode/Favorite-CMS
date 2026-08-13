import pytest

from backend.core import Kernel
from backend.engines.media import MediaEngine, MediaType
from backend.engines.media.engine import InvalidMedia, MediaError
from backend.engines.permissions import PermissionDenied
from backend.tests.platform_data.conftest import authenticated


def _permissions(kernel: Kernel) -> None:
    assert kernel.container.resolve("engine.media", MediaEngine).ready


def test_media_uses_storage_for_bytes_and_persists_safe_metadata(data_kernel: Kernel) -> None:
    _permissions(data_kernel); engine = data_kernel.container.resolve("engine.media", MediaEngine); auth = authenticated(data_kernel)
    item = engine.upload(media_type=MediaType.IMAGE, file_name="photo.png", mime_type="image/png",
                         data=b"png-bytes", metadata={"width": 10}, public=False, authentication=auth)
    assert item.size == 9 and engine.retrieve(item.media_id, auth) == b"png-bytes"
    assert engine.update_metadata(item.media_id, {"width": 20}, auth).metadata["width"] == 20
    engine.register_processor("tests.reverse", lambda data, options: data[::-1])
    assert engine.process(item.media_id, "tests.reverse", {}, auth) == b"setyb-gnp"
    assert engine.retrieve(item.media_id, auth) == b"png-bytes"
    assert engine.delivery(item.media_id, auth).reference == f"media:{item.media_id}"
    assert not hasattr(item, "storage_identifier")


def test_media_access_path_safety_missing_and_delete(data_kernel: Kernel) -> None:
    _permissions(data_kernel); engine = data_kernel.container.resolve("engine.media", MediaEngine); auth = authenticated(data_kernel)
    with pytest.raises(InvalidMedia):
        engine.upload(media_type=MediaType.IMAGE, file_name="../secret", mime_type="image/png", data=b"x", metadata={}, public=False, authentication=auth)
    item = engine.upload(media_type=MediaType.DOCUMENT, file_name="safe.pdf", mime_type="application/pdf", data=b"pdf", metadata={}, public=False, authentication=auth)
    with pytest.raises(PermissionDenied): engine.retrieve(item.media_id)
    engine.delete(item.media_id, auth)
    with pytest.raises(MediaError): engine.get(item.media_id, auth)


def test_media_storage_provider_failure_does_not_create_resource(
    data_kernel: Kernel, monkeypatch: pytest.MonkeyPatch
) -> None:
    from backend.engines.storage import StorageEngine, StorageError
    _permissions(data_kernel); engine = data_kernel.container.resolve("engine.media", MediaEngine); auth = authenticated(data_kernel)
    storage = data_kernel.container.resolve("engine.storage", StorageEngine)
    monkeypatch.setattr(storage, "store", lambda *args, **kwargs: (_ for _ in ()).throw(StorageError("unavailable")))
    with pytest.raises(StorageError):
        engine.upload(media_type=MediaType.IMAGE, file_name="safe.png", mime_type="image/png", data=b"bytes", metadata={}, public=False, authentication=auth)


def test_public_media_requires_explicit_public_permission(data_kernel: Kernel) -> None:
    _permissions(data_kernel); engine = data_kernel.container.resolve("engine.media", MediaEngine); auth = authenticated(data_kernel)
    item = engine.upload(media_type=MediaType.AUDIO, file_name="audio.mp3", mime_type="audio/mpeg", data=b"audio", metadata={}, public=True, authentication=auth)
    assert engine.retrieve(item.media_id) == b"audio"


def test_media_list_is_deterministic_and_permission_filtered(data_kernel: Kernel) -> None:
    _permissions(data_kernel); engine = data_kernel.container.resolve("engine.media", MediaEngine); auth = authenticated(data_kernel)
    first = engine.upload(media_type=MediaType.DOCUMENT, file_name="first.txt", mime_type="text/plain", data=b"first", metadata={}, public=False, authentication=auth)
    second = engine.upload(media_type=MediaType.DOCUMENT, file_name="second.txt", mime_type="text/plain", data=b"second", metadata={}, public=True, authentication=auth)
    assert {item.media_id for item in engine.list(auth)} == {first.media_id, second.media_id}
    assert [item.media_id for item in engine.list(auth)] == sorted((first.media_id, second.media_id))
    assert [item.media_id for item in engine.list()] == [second.media_id]


def test_media_processing_failure_preserves_original(data_kernel: Kernel) -> None:
    _permissions(data_kernel); engine = data_kernel.container.resolve("engine.media", MediaEngine); auth = authenticated(data_kernel)
    item = engine.upload(media_type=MediaType.IMAGE, file_name="image.png", mime_type="image/png", data=b"original", metadata={}, public=False, authentication=auth)
    engine.register_processor("tests.fail", lambda data, options: (_ for _ in ()).throw(RuntimeError("failure")))
    with pytest.raises(MediaError, match="processing"): engine.process(item.media_id, "tests.fail", {}, auth)
    assert engine.retrieve(item.media_id, auth) == b"original"
