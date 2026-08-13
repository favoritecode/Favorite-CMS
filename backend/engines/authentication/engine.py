"""Email/password authentication and signed JWT context management.

Raw credentials stay inside this boundary. Authorization is intentionally not
performed here.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
from typing import Callable
from uuid import UUID, uuid4

from sqlalchemy import Column, MetaData, String, Table, insert, select, update
from sqlalchemy.exc import IntegrityError

from backend.config import Configuration, SecretValue
from backend.core.container import ServiceContainer
from backend.database import DatabaseEngine
from backend.database.migrations import DatabaseMigrationEngine, Migration
from backend.engines.errors import ApplicationFailure, ValidationFailure
from backend.engines.users import AccountState, User, UserEngine


class AuthenticationError(ApplicationFailure):
    pass


class InvalidAuthenticationRequest(ValidationFailure):
    pass


class CredentialToken:
    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    _value: str

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "CredentialToken('[REDACTED]')"

    def __str__(self) -> str:
        return "[REDACTED]"


@dataclass(frozen=True)
class AuthenticationContext:
    authenticated: bool
    user_id: str | None = None
    method: str | None = None
    context_id: str | None = None
    expires_at: str | None = None
    _proof: str | None = field(default=None, repr=False, compare=False)

    @classmethod
    def anonymous(cls) -> AuthenticationContext:
        return cls(False)


@dataclass(frozen=True, repr=False)
class AuthenticationResult:
    success: bool
    context: AuthenticationContext
    token: CredentialToken | None = None
    failure: str | None = None

    def __repr__(self) -> str:
        return f"AuthenticationResult(success={self.success!r}, context={self.context!r})"


class PasswordHasher:
    """Versioned PBKDF2-HMAC-SHA256 storage format using per-password salts."""

    algorithm = "pbkdf2_sha256"

    def __init__(self, *, iterations: int = 600_000) -> None:
        if iterations < 100_000:
            raise ValueError("Password hashing work factor is unsafe")
        self._iterations = iterations

    def hash(self, password: str) -> str:
        _password(password)
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self._iterations)
        return "$".join(
            (self.algorithm, str(self._iterations), _encode(salt), _encode(digest))
        )

    def verify(self, password: str, encoded: str) -> bool:
        try:
            algorithm, iterations, salt, expected = encoded.split("$", 3)
            if algorithm != self.algorithm:
                return False
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), _decode(salt), int(iterations)
            )
            return hmac.compare_digest(actual, _decode(expected))
        except (ValueError, TypeError):
            return False


_metadata = MetaData()
_credentials = Table(
    "favorite_auth_password_credentials",
    _metadata,
    Column("user_id", String(36), primary_key=True),
    Column("password_hash", String(512), nullable=False),
    Column("credential_version", String(32), nullable=False),
)
_revoked = Table(
    "favorite_auth_revoked_contexts",
    _metadata,
    Column("context_id", String(36), primary_key=True),
    Column("expires_at", String(64), nullable=False),
)


def authentication_schema_migration() -> Migration:
    return Migration(
        "platform.authentication.001",
        "engine.authentication",
        lambda connection: _metadata.create_all(connection, tables=[_credentials, _revoked]),
        dependencies=("platform.user.001",),
    )


class AuthenticationEngine:
    engine_id = "authentication"
    dependencies = ("database", "migrations", "users")

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        hasher: PasswordHasher | None = None,
    ) -> None:
        self._database: DatabaseEngine | None = None
        self._users: UserEngine | None = None
        self._configuration: Configuration | None = None
        self._secret: bytes | None = None
        self._lifetime = 0
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._hasher = hasher or PasswordHasher()
        self._dummy_hash = self._hasher.hash("favorite-cms-invalid-credential")
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._database = container.resolve("engine.database", DatabaseEngine)
        self._users = container.resolve("engine.users", UserEngine)
        self._configuration = container.resolve("core.configuration", Configuration)
        migrations = container.resolve("engine.migrations", DatabaseMigrationEngine)
        migrations.register(authentication_schema_migration())
        container.register("engine.authentication", self)

    def start(self) -> None:
        configuration = self._configuration_required()
        configured = configuration.get("authentication.jwt_secret", SecretValue).reveal()
        environment = configuration.get("environment", str)
        if not configured:
            if environment == "production":
                raise AuthenticationError("Authentication configuration is unavailable")
            configured = secrets.token_urlsafe(48)
        if len(configured.encode()) < 32:
            raise AuthenticationError("Authentication configuration is invalid")
        lifetime = configuration.get("authentication.token_lifetime_seconds", int)
        if lifetime <= 0:
            raise AuthenticationError("Authentication lifetime is invalid")
        self._secret = configured.encode()
        self._lifetime = lifetime
        self.ready = True

    def shutdown(self) -> None:
        self.ready = False
        self._secret = None
        self._lifetime = 0

    def set_password(self, user_id: str, password: str) -> None:
        self._require_ready()
        user = self._users_required().get(user_id)
        encoded = self._hasher.hash(password)
        with self._database_required().transaction() as session:
            current = session.execute(
                select(_credentials.c.credential_version).where(_credentials.c.user_id == user.user_id)
            ).scalar_one_or_none()
            if current is None:
                session.execute(
                    insert(_credentials).values(
                        user_id=user.user_id, password_hash=encoded, credential_version="1"
                    )
                )
            else:
                session.execute(
                    update(_credentials)
                    .where(_credentials.c.user_id == user.user_id)
                    .values(password_hash=encoded, credential_version=str(int(current) + 1))
                )

    def login(self, *, email: str, password: str) -> AuthenticationResult:
        self._require_ready()
        try:
            user = self._users_required().find_by_email(email)
        except ValidationFailure:
            user = None
        credential = None if user is None else self._credential(user.user_id)
        # Always perform a password derivation to reduce identity-enumeration timing differences.
        encoded = credential[0] if credential is not None else self._dummy_hash
        verified = self._hasher.verify(password, encoded)
        if user is None or credential is None or not verified:
            return _failed("invalid_authentication")
        if user.state is not AccountState.ACTIVE:
            return _failed("invalid_authentication")
        token, context = self._issue(user, credential[1])
        return AuthenticationResult(True, context, token)

    def resolve(self, token: str | CredentialToken | None) -> AuthenticationContext:
        if not self.ready or token is None:
            return AuthenticationContext.anonymous()
        raw = token.reveal() if isinstance(token, CredentialToken) else token
        try:
            claims = self._decode(raw)
            user = self._users_required().get(claims["sub"])
            if user.state is not AccountState.ACTIVE:
                return AuthenticationContext.anonymous()
            credential = self._credential(user.user_id)
            if credential is None or credential[1] != claims["cv"]:
                return AuthenticationContext.anonymous()
            if self._is_revoked(claims["jti"]):
                return AuthenticationContext.anonymous()
            context = AuthenticationContext(
                True, user.user_id, "password", claims["jti"],
                datetime.fromtimestamp(claims["exp"], timezone.utc).isoformat(),
            )
            return self._seal_context(context)
        except Exception:
            return AuthenticationContext.anonymous()

    def is_context_valid(self, context: AuthenticationContext) -> bool:
        """Validate that a context was issued here and remains currently trusted."""
        if not self.ready or not context.authenticated or context._proof is None:
            return False
        expected = self._context_proof(context)
        if not hmac.compare_digest(expected, context._proof):
            return False
        if context.expires_at is None or context.user_id is None or context.context_id is None:
            return False
        try:
            expires = datetime.fromisoformat(context.expires_at)
            user = self._users_required().get(context.user_id)
            return (
                expires > self._now()
                and user.state is AccountState.ACTIVE
                and not self._is_revoked(context.context_id)
            )
        except Exception:
            return False

    def logout(self, token: str | CredentialToken) -> bool:
        context = self.resolve(token)
        return self.revoke_context(context)

    def revoke_context(self, context: AuthenticationContext) -> bool:
        if not self.is_context_valid(context) or context.context_id is None or context.expires_at is None:
            return False
        try:
            with self._database_required().transaction() as session:
                session.execute(
                    insert(_revoked).values(
                        context_id=context.context_id, expires_at=context.expires_at
                    )
                )
            return True
        except IntegrityError:
            return False

    def _issue(self, user: User, credential_version: str) -> tuple[CredentialToken, AuthenticationContext]:
        now = self._now()
        expires = now + timedelta(seconds=self._lifetime)
        context_id = str(uuid4())
        claims: dict[str, object] = {
            "iss": "favorite-cms", "sub": user.user_id, "jti": context_id,
            "iat": int(now.timestamp()), "exp": int(expires.timestamp()),
            "cv": credential_version, "amr": "password",
        }
        token = CredentialToken(self._encode(claims))
        context = AuthenticationContext(
            True, user.user_id, "password", context_id, expires.isoformat()
        )
        return token, self._seal_context(context)

    def _seal_context(self, context: AuthenticationContext) -> AuthenticationContext:
        return AuthenticationContext(
            context.authenticated, context.user_id, context.method, context.context_id,
            context.expires_at, self._context_proof(context),
        )

    def _context_proof(self, context: AuthenticationContext) -> str:
        values = (
            str(context.authenticated), context.user_id or "", context.method or "",
            context.context_id or "", context.expires_at or "",
        )
        return hmac.new(
            self._secret_required(), "\x1f".join(values).encode(), hashlib.sha256
        ).hexdigest()

    def _encode(self, claims: dict[str, object]) -> str:
        header = _encode_json({"alg": "HS256", "typ": "JWT"})
        payload = _encode_json(claims)
        body = f"{header}.{payload}"
        signature = hmac.new(self._secret_required(), body.encode(), hashlib.sha256).digest()
        return f"{body}.{_encode(signature)}"

    def _decode(self, token: str) -> dict[str, object]:
        if not isinstance(token, str) or len(token) > 8192:
            raise InvalidAuthenticationRequest("Authentication context is invalid")
        header_part, payload_part, signature_part = token.split(".")
        body = f"{header_part}.{payload_part}"
        expected = hmac.new(self._secret_required(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _decode(signature_part)):
            raise InvalidAuthenticationRequest("Authentication context is invalid")
        header = json.loads(_decode(header_part))
        claims = json.loads(_decode(payload_part))
        if header != {"alg": "HS256", "typ": "JWT"} or claims.get("iss") != "favorite-cms":
            raise InvalidAuthenticationRequest("Authentication context is invalid")
        required = ("sub", "jti", "iat", "exp", "cv")
        if any(key not in claims for key in required):
            raise InvalidAuthenticationRequest("Authentication context is invalid")
        UUID(str(claims["sub"])); UUID(str(claims["jti"]))
        if not isinstance(claims["iat"], int) or not isinstance(claims["exp"], int):
            raise InvalidAuthenticationRequest("Authentication context is invalid")
        now = int(self._now().timestamp())
        if claims["exp"] <= now or claims["iat"] > now:
            raise InvalidAuthenticationRequest("Authentication context is invalid")
        return claims

    def _credential(self, user_id: str) -> tuple[str, str] | None:
        with self._database_required().session() as session:
            row = session.execute(
                select(_credentials.c.password_hash, _credentials.c.credential_version)
                .where(_credentials.c.user_id == user_id)
            ).first()
        return None if row is None else (row[0], row[1])

    def _is_revoked(self, context_id: object) -> bool:
        with self._database_required().session() as session:
            return session.execute(
                select(_revoked.c.context_id).where(_revoked.c.context_id == str(context_id))
            ).scalar_one_or_none() is not None

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise AuthenticationError("Authentication clock is invalid")
        return value.astimezone(timezone.utc)

    def _require_ready(self) -> None:
        if not self.ready:
            raise AuthenticationError("Authentication Engine is unavailable")

    def _database_required(self) -> DatabaseEngine:
        if self._database is None:
            raise AuthenticationError("Authentication persistence is unavailable")
        return self._database

    def _users_required(self) -> UserEngine:
        if self._users is None:
            raise AuthenticationError("User identity is unavailable")
        return self._users

    def _configuration_required(self) -> Configuration:
        if self._configuration is None:
            raise AuthenticationError("Authentication configuration is unavailable")
        return self._configuration

    def _secret_required(self) -> bytes:
        if self._secret is None:
            raise AuthenticationError("Authentication Engine is unavailable")
        return self._secret


def _failed(reason: str) -> AuthenticationResult:
    return AuthenticationResult(False, AuthenticationContext.anonymous(), failure=reason)


def _password(value: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise InvalidAuthenticationRequest("Credential is invalid")


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    if not isinstance(value, str) or not value or "=" in value:
        raise ValueError("Base64 value is invalid")
    decoded = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    if _encode(decoded) != value:
        raise ValueError("Base64 value is not canonical")
    return decoded


def _encode_json(value: dict[str, object]) -> str:
    return _encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())
