import pytest

from backend.core import Kernel
from backend.engines.content import (
    ContentEngine, ContentField, ContentQuery, ContentState, ContentType, FieldKind,
)
from backend.engines.content.engine import InvalidContent
from backend.engines.permissions import PermissionDenied
from backend.tests.platform_data.conftest import authenticated, permission


def _contract(kernel: Kernel) -> ContentType:
    permissions = {action: f"tests.content.{action}" for action in ("create", "read", "update", "delete", "publish", "archive")}
    for action, permission_id in permissions.items():
        permission(kernel, permission_id, action, "content", allow_owner=True,
                   allow_public=action == "read")
    return ContentType("tests.generic", "tests", "Generic", (ContentField("body", FieldKind.STRING, True),), permissions)


def test_content_lifecycle_query_and_persistence(data_kernel: Kernel) -> None:
    engine = data_kernel.container.resolve("engine.content", ContentEngine); engine.register_type(_contract(data_kernel))
    auth = authenticated(data_kernel)
    created = engine.create("tests.generic", title="Title", data={"body": "Text"}, metadata={}, authentication=auth)
    assert created.state is ContentState.DRAFT and engine.get(created.content_id, auth).title == "Title"
    changed = engine.update(created.content_id, title="Changed", data={"body": "New"}, metadata={"label": "x"}, authentication=auth)
    published = engine.publish(changed.content_id, auth); archived = engine.archive(changed.content_id, auth)
    assert published.state is ContentState.PUBLISHED and archived.state is ContentState.ARCHIVED
    assert engine.query(ContentQuery(type_id="tests.generic", state=ContentState.ARCHIVED), auth) == (archived,)


def test_content_validation_transition_and_permission_fail_closed(data_kernel: Kernel) -> None:
    engine = data_kernel.container.resolve("engine.content", ContentEngine); engine.register_type(_contract(data_kernel))
    auth = authenticated(data_kernel)
    with pytest.raises(InvalidContent): engine.create("tests.generic", title="Bad", data={}, metadata={}, authentication=auth)
    created = engine.create("tests.generic", title="Good", data={"body": "Text"}, metadata={}, authentication=auth)
    with pytest.raises(InvalidContent): engine.archive(created.content_id, auth)
    with pytest.raises(PermissionDenied): engine.get(created.content_id)
    assert engine.get(created.content_id, auth).state is ContentState.DRAFT


def test_published_content_is_public_only_through_explicit_permission(data_kernel: Kernel) -> None:
    engine = data_kernel.container.resolve("engine.content", ContentEngine); engine.register_type(_contract(data_kernel))
    auth = authenticated(data_kernel); item = engine.create("tests.generic", title="Public", data={"body": "Text"}, metadata={}, authentication=auth)
    engine.publish(item.content_id, auth)
    assert engine.get(item.content_id).title == "Public"
    engine.delete(item.content_id, auth)
    assert engine.query(ContentQuery(type_id="tests.generic"), auth) == ()
