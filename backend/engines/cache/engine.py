"""Optional scoped cache acceleration with safe provider degradation."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic
import re
from typing import Protocol

from backend.config import Configuration
from backend.core.container import ServiceContainer
from backend.engines.logging import LogCategory, LogSource, LogSourceKind, LoggingEngine


_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


@dataclass(frozen=True)
class CacheScope:
    name: str
    owner: str

    def __post_init__(self) -> None:
        if not _PART.fullmatch(self.name) or not _PART.fullmatch(self.owner):
            raise ValueError("Cache Scope is invalid")

    @property
    def key(self) -> str:
        return f"{self.owner}:{self.name}"


@dataclass(frozen=True)
class CacheKey:
    scope: CacheScope
    identifier: str

    def __post_init__(self) -> None:
        if not _PART.fullmatch(self.identifier):
            raise ValueError("Cache Key is invalid")


@dataclass(frozen=True)
class CacheResult:
    hit: bool
    value: object | None = None


class CacheProvider(Protocol):
    def get(self, key: str) -> CacheResult: ...
    def set(self, key: str, value: object, ttl_seconds: float | None) -> None: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...
    def clear_prefix(self, prefix: str) -> None: ...
    def healthcheck(self) -> bool: ...


@dataclass
class _Entry:
    value: object
    expires_at: float | None


class InMemoryCacheProvider:
    def __init__(self) -> None:
        self._entries: dict[str, _Entry] = {}
        self._lock = RLock()

    def get(self, key: str) -> CacheResult:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return CacheResult(False)
            if entry.expires_at is not None and monotonic() >= entry.expires_at:
                del self._entries[key]
                return CacheResult(False)
            return CacheResult(True, entry.value)

    def set(self, key: str, value: object, ttl_seconds: float | None) -> None:
        expires_at = None if ttl_seconds is None else monotonic() + ttl_seconds
        with self._lock:
            self._entries[key] = _Entry(value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key).hit

    def clear_prefix(self, prefix: str) -> None:
        with self._lock:
            for key in tuple(self._entries):
                if key.startswith(prefix):
                    del self._entries[key]

    def healthcheck(self) -> bool:
        return True


class CacheEngine:
    engine_id = "cache"
    dependencies: tuple[str, ...] = ()

    def __init__(self, provider: CacheProvider | None = None) -> None:
        self._provider = provider
        self._enabled = True
        self._logging: LoggingEngine | None = None
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        configuration = container.resolve("core.configuration", Configuration)
        self._enabled = configuration.get("cache.enabled", bool)
        self._logging = container.resolve("core.logging", LoggingEngine)
        container.register("engine.cache", self)

    def start(self) -> None:
        if not self._enabled:
            self.ready = True
            return
        if self._provider is None:
            self._provider = InMemoryCacheProvider()
        self.ready = self._safe_healthcheck()
        if not self.ready:
            self._log_failure("Cache Provider is unavailable")

    def shutdown(self) -> None:
        self.ready = False

    def healthcheck(self) -> bool:
        return self._safe_healthcheck() if self._enabled else True

    def get(self, key: CacheKey) -> CacheResult:
        if not self._available():
            return CacheResult(False)
        try:
            return self._provider.get(self._provider_key(key))  # type: ignore[union-attr]
        except Exception:
            self._degrade("Cache retrieval failed")
            return CacheResult(False)

    def set(self, key: CacheKey, value: object, *, ttl_seconds: float | None = None) -> bool:
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("Cache TTL must be positive")
        if not self._available():
            return False
        try:
            self._provider.set(self._provider_key(key), value, ttl_seconds)  # type: ignore[union-attr]
            return True
        except Exception:
            self._degrade("Cache storage failed")
            return False

    def delete(self, key: CacheKey) -> bool:
        if not self._available():
            return False
        try:
            self._provider.delete(self._provider_key(key))  # type: ignore[union-attr]
            return True
        except Exception:
            self._degrade("Cache invalidation failed")
            return False

    def exists(self, key: CacheKey) -> bool:
        return self.get(key).hit

    def clear(self, scope: CacheScope) -> bool:
        if not self._available():
            return False
        try:
            self._provider.clear_prefix(f"{scope.key}:")  # type: ignore[union-attr]
            return True
        except Exception:
            self._degrade("Cache clear failed")
            return False

    def _provider_key(self, key: CacheKey) -> str:
        return f"{key.scope.key}:{key.identifier}"

    def _available(self) -> bool:
        return self._enabled and self.ready and self._provider is not None

    def _safe_healthcheck(self) -> bool:
        try:
            return self._provider is not None and self._provider.healthcheck()
        except Exception:
            return False

    def _degrade(self, message: str) -> None:
        self.ready = False
        self._log_failure(message)

    def _log_failure(self, message: str) -> None:
        if self._logging is not None:
            self._logging.warning(
                message,
                source=LogSource(LogSourceKind.ENGINE, "cache"),
                category=LogCategory.ENGINE,
            )
