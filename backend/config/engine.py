"""Typed, deterministic bootstrap configuration.

Configuration is intentionally distinct from application-managed Settings.
Only explicitly supplied sources are read; there are no hidden global sources.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
from types import MappingProxyType
from typing import Any, Generic, Mapping, Protocol, TypeVar, cast

T = TypeVar("T")


class ConfigurationError(ValueError):
    """Raised when a configuration contract cannot be satisfied."""


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(frozen=True, repr=False)
class SecretValue:
    """A protected configuration value whose representation is always masked."""

    _value: str

    def reveal(self) -> str:
        """Return the secret to an explicitly authorized infrastructure consumer."""
        return self._value

    def __repr__(self) -> str:
        return "SecretValue('[REDACTED]')"

    def __str__(self) -> str:
        return "[REDACTED]"


@dataclass(frozen=True)
class ConfigField(Generic[T]):
    key: str
    value_type: type[T]
    required: bool = False
    default: T | None = None
    secret: bool = False
    allowed: frozenset[T] | None = None


@dataclass(frozen=True)
class ConfigurationSchema:
    fields: tuple[ConfigField[Any], ...]

    def __post_init__(self) -> None:
        keys = [field.key for field in self.fields]
        if len(keys) != len(set(keys)):
            raise ConfigurationError("Configuration schema contains duplicate keys")


class ConfigurationSource(Protocol):
    """An explicit source of untrusted bootstrap values."""

    name: str
    priority: int

    def load(self) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class MappingSource:
    name: str
    values: Mapping[str, object]
    priority: int

    def load(self) -> Mapping[str, object]:
        return dict(self.values)


@dataclass(frozen=True)
class EnvironmentSource:
    """Reads only the explicit environment-key mapping supplied by its caller."""

    keys: Mapping[str, str]
    priority: int = 100
    name: str = "environment"

    def load(self) -> Mapping[str, object]:
        return {
            config_key: os.environ[environment_key]
            for config_key, environment_key in self.keys.items()
            if environment_key in os.environ
        }


class Configuration:
    """Immutable validated effective bootstrap configuration."""

    def __init__(self, values: Mapping[str, object], secret_keys: frozenset[str]) -> None:
        self._values = MappingProxyType(dict(values))
        self._secret_keys = secret_keys

    @classmethod
    def resolve(
        cls,
        schema: ConfigurationSchema,
        sources: tuple[ConfigurationSource, ...],
    ) -> Configuration:
        priorities = [source.priority for source in sources]
        if len(priorities) != len(set(priorities)):
            raise ConfigurationError("Configuration source priorities must be unique")

        supplied: dict[str, object] = {}
        for source in sorted(sources, key=lambda item: item.priority):
            supplied.update(source.load())

        known_keys = {field.key for field in schema.fields}
        unknown = sorted(set(supplied) - known_keys)
        if unknown:
            raise ConfigurationError(f"Unknown configuration keys: {', '.join(unknown)}")

        values: dict[str, object] = {}
        secret_keys: set[str] = set()
        for field in schema.fields:
            raw = supplied.get(field.key, field.default)
            if raw is None and field.required:
                raise ConfigurationError(f"Missing required configuration key: {field.key}")
            if raw is None:
                continue
            value = _convert(field.key, raw, field.value_type)
            if field.allowed is not None and value not in field.allowed:
                raise ConfigurationError(f"Configuration key has an unsupported value: {field.key}")
            if field.secret:
                secret_keys.add(field.key)
                value = SecretValue(str(value))
            values[field.key] = value
        return cls(values, frozenset(secret_keys))

    def get(self, key: str, expected_type: type[T]) -> T:
        if key not in self._values:
            raise ConfigurationError(f"Configuration key is unavailable: {key}")
        value = self._values[key]
        if not isinstance(value, expected_type):
            raise ConfigurationError(f"Configuration key has an unexpected type: {key}")
        return cast(T, value)

    def snapshot(self) -> Mapping[str, object]:
        """Return immutable diagnostics with secret values excluded."""
        return MappingProxyType(
            {key: value for key, value in self._values.items() if key not in self._secret_keys}
        )

    def is_configured(self, key: str) -> bool:
        """Report presence without revealing configuration values, including secrets."""
        if key not in self._values:
            return False
        value = self._values[key]
        if isinstance(value, SecretValue):
            return bool(value.reveal().strip())
        return bool(value) if isinstance(value, (str, bool)) else True


def _convert(key: str, value: object, target: type[T]) -> T:
    if isinstance(value, target):
        return value
    if target is bool and isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return cast(T, True)
        if normalized in {"false", "0", "no"}:
            return cast(T, False)
    if target is int and isinstance(value, str):
        try:
            return cast(T, int(value))
        except ValueError:
            pass
    if target is str and isinstance(value, (str, int, bool)):
        return cast(T, str(value))
    raise ConfigurationError(f"Configuration key has an invalid type: {key}")


BOOTSTRAP_SCHEMA = ConfigurationSchema(
    fields=(
        ConfigField("environment", str, default=Environment.DEVELOPMENT.value,
                    allowed=frozenset(item.value for item in Environment)),
        ConfigField("debug", bool, default=False),
        ConfigField("host", str, default="127.0.0.1"),
        ConfigField("port", int, default=8000),
        ConfigField("database.url", str, default="sqlite:///storage/favorite-cms.db", secret=True),
        ConfigField("storage.root", str, default="storage/files", secret=True),
        ConfigField("storage.provider", str, default="local", allowed=frozenset({"local", "mounted"})),
        ConfigField("cache.enabled", bool, default=True),
        ConfigField("authentication.jwt_secret", str, default="", secret=True),
        ConfigField("authentication.token_lifetime_seconds", int, default=900),
        ConfigField("theme.active", str, default=""),
        ConfigField("tools.worker_url", str, default=""),
        ConfigField("tools.worker_token", str, default="", secret=True),
        ConfigField("tools.timeout_seconds", int, default=15),
    )
)


def create_bootstrap_configuration() -> Configuration:
    """Resolve the documented Phase 0 environment template.

    Precedence is explicit: schema defaults, then environment values.
    """
    environment = EnvironmentSource(
        keys={
            "environment": "FAVORITE_ENV",
            "debug": "FAVORITE_DEBUG",
            "host": "FAVORITE_HOST",
            "port": "FAVORITE_PORT",
            "database.url": "FAVORITE_DATABASE_URL",
            "storage.root": "FAVORITE_STORAGE_ROOT",
            "storage.provider": "FAVORITE_STORAGE_PROVIDER",
            "cache.enabled": "FAVORITE_CACHE_ENABLED",
            "authentication.jwt_secret": "FAVORITE_AUTH_JWT_SECRET",
            "authentication.token_lifetime_seconds": "FAVORITE_AUTH_TOKEN_LIFETIME_SECONDS",
            "theme.active": "FAVORITE_ACTIVE_THEME",
            "tools.worker_url": "FAVORITE_TOOL_WORKER_URL",
            "tools.worker_token": "FAVORITE_TOOL_WORKER_TOKEN",
            "tools.timeout_seconds": "FAVORITE_TOOL_TIMEOUT_SECONDS",
        }
    )
    return Configuration.resolve(BOOTSTRAP_SCHEMA, (environment,))
