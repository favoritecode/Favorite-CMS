"""User Resource ownership and persistence.

Authentication credentials and authorization policy deliberately do not live
in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Column, MetaData, String, Table, insert, select, update
from sqlalchemy.exc import IntegrityError

from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.errors import ApplicationFailure, ValidationFailure


class AccountState(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESTRICTED = "restricted"


class UserError(ApplicationFailure):
    pass


class UserNotFound(UserError):
    pass


class InvalidUser(ValidationFailure):
    pass


@dataclass(frozen=True)
class PublicUser:
    user_id: str
    display_name: str
    role: str
    state: AccountState
    profile_image_id: str | None


@dataclass(frozen=True, repr=False)
class User:
    user_id: str
    email: str
    display_name: str
    role: str
    state: AccountState
    profile_image_id: str | None

    def public(self) -> PublicUser:
        return PublicUser(
            self.user_id, self.display_name, self.role, self.state, self.profile_image_id
        )

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id!r}, state={self.state.value!r})"


_metadata = MetaData()
_users = Table(
    "favorite_users",
    _metadata,
    Column("user_id", String(36), primary_key=True),
    Column("email", String(320), nullable=False, unique=True),
    Column("display_name", String(255), nullable=False),
    Column("role", String(255), nullable=False),
    Column("state", String(32), nullable=False),
    Column("profile_image_id", String(255), nullable=True),
)


def user_schema_migration() -> Migration:
    return Migration(
        "platform.user.001",
        "engine.user",
        lambda connection: _metadata.create_all(connection, tables=[_users]),
    )


class UserEngine:
    engine_id = "users"
    dependencies = ("database", "migrations")

    def __init__(self) -> None:
        self._database: DatabaseEngine | None = None
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        migrations = container.resolve("engine.migrations", DatabaseMigrationEngine)
        migrations.register(user_schema_migration())
        container.register("engine.users", self)

    def start(self) -> None:
        if self._database is None or not self._database.ready:
            raise UserError("User persistence is unavailable")
        self.ready = True

    def shutdown(self) -> None:
        self.ready = False

    def create(self, *, email: str, display_name: str, role: str) -> User:
        self._require_ready()
        normalized_email = _email(email)
        name = _required(display_name, "Display name")
        normalized_role = _required(role, "Role")
        if self.find_by_email(normalized_email) is not None:
            raise InvalidUser("User identity is already registered")
        user = User(str(uuid4()), normalized_email, name, normalized_role, AccountState.ACTIVE, None)
        try:
            with self._database_required().transaction() as session:
                session.execute(insert(_users).values(**_values(user)))
        except IntegrityError as exc:
            raise InvalidUser("User identity is already registered") from exc
        return user

    def get(self, user_id: str) -> User:
        self._require_ready()
        identifier = _identifier(user_id)
        with self._database_required().session() as session:
            row = session.execute(select(_users).where(_users.c.user_id == identifier)).mappings().first()
        if row is None:
            raise UserNotFound("User was not found")
        return _from_row(row)

    def find_by_email(self, email: str) -> User | None:
        self._require_ready()
        normalized = _email(email)
        with self._database_required().session() as session:
            row = session.execute(select(_users).where(_users.c.email == normalized)).mappings().first()
        return None if row is None else _from_row(row)

    def update_profile(
        self, user_id: str, *, display_name: str, profile_image_id: str | None = None
    ) -> User:
        current = self.get(user_id)
        name = _required(display_name, "Display name")
        image = None if profile_image_id is None else _required(profile_image_id, "Profile image")
        with self._database_required().transaction() as session:
            session.execute(
                update(_users)
                .where(_users.c.user_id == current.user_id)
                .values(display_name=name, profile_image_id=image)
            )
        return self.get(current.user_id)

    def change_state(self, user_id: str, state: AccountState) -> User:
        current = self.get(user_id)
        if not isinstance(state, AccountState):
            raise InvalidUser("User account state is invalid")
        with self._database_required().transaction() as session:
            session.execute(
                update(_users).where(_users.c.user_id == current.user_id).values(state=state.value)
            )
        return self.get(current.user_id)

    def _database_required(self) -> DatabaseEngine:
        if self._database is None:
            raise UserError("User persistence is unavailable")
        return self._database

    def _require_ready(self) -> None:
        if not self.ready:
            raise UserError("User Engine is unavailable")


def _values(user: User) -> dict[str, str | None]:
    return {
        "user_id": user.user_id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "state": user.state.value,
        "profile_image_id": user.profile_image_id,
    }


def _from_row(row: object) -> User:
    mapping = row  # SQLAlchemy RowMapping at runtime.
    return User(
        mapping["user_id"], mapping["email"], mapping["display_name"], mapping["role"],
        AccountState(mapping["state"]), mapping["profile_image_id"],
    )


def _identifier(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, TypeError) as exc:
        raise InvalidUser("User identifier is invalid") from exc


def _email(value: str) -> str:
    normalized = value.strip().casefold()
    if not normalized or len(normalized) > 320 or normalized.count("@") != 1:
        raise InvalidUser("User identity is invalid")
    local, domain = normalized.split("@", 1)
    if not local or not domain or "." not in domain:
        raise InvalidUser("User identity is invalid")
    return normalized


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 255:
        raise InvalidUser(f"{label} is invalid")
    return normalized
