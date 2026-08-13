import pytest
from sqlalchemy import inspect

from backend.core import Kernel
from backend.database import DatabaseEngine
from backend.engines.users import AccountState, UserEngine
from backend.engines.users.engine import InvalidUser


def test_user_creation_persistence_and_safe_representation(identity_kernel: Kernel) -> None:
    users = identity_kernel.container.resolve("engine.users", UserEngine)
    created = users.create(email=" Member@Example.COM ", display_name="Member", role="member")
    loaded = users.get(created.user_id)
    assert loaded.email == "member@example.com"
    assert loaded.state is AccountState.ACTIVE
    assert loaded.public().display_name == "Member"
    assert not hasattr(loaded.public(), "email")
    assert "member@example.com" not in repr(loaded)


def test_user_identity_is_unique_and_input_is_validated(identity_kernel: Kernel) -> None:
    users = identity_kernel.container.resolve("engine.users", UserEngine)
    users.create(email="one@example.com", display_name="One", role="member")
    with pytest.raises(InvalidUser, match="already"):
        users.create(email="ONE@example.com", display_name="Other", role="member")
    with pytest.raises(InvalidUser):
        users.create(email="invalid", display_name="Other", role="member")
    with pytest.raises(InvalidUser):
        users.create(email="two@example.com", display_name=" ", role="member")


def test_profile_and_account_state_changes_are_isolated(identity_kernel: Kernel) -> None:
    users = identity_kernel.container.resolve("engine.users", UserEngine)
    first = users.create(email="first@example.com", display_name="First", role="member")
    second = users.create(email="second@example.com", display_name="Second", role="member")
    changed = users.update_profile(first.user_id, display_name="Updated", profile_image_id="media-1")
    restricted = users.change_state(first.user_id, AccountState.RESTRICTED)
    assert changed.display_name == "Updated" and changed.profile_image_id == "media-1"
    assert restricted.state is AccountState.RESTRICTED
    assert users.get(second.user_id).display_name == "Second"
    with pytest.raises(InvalidUser):
        users.update_profile(first.user_id, display_name=" ")
    assert users.get(first.user_id).display_name == "Updated"


def test_user_schema_exists_only_after_explicit_migration(identity_kernel: Kernel) -> None:
    database = identity_kernel.container.resolve("engine.database", DatabaseEngine)
    assert "favorite_users" in inspect(database.connection_engine()).get_table_names()
