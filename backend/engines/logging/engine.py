"""Provider-neutral structured logging with fail-safe output dispatch."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import IntEnum, StrEnum
import json
from types import MappingProxyType
from typing import Mapping, Protocol
from uuid import uuid4


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogCategory(StrEnum):
    CORE = "core"
    ENGINE = "engine"
    EXTENSION = "extension"
    REQUEST = "request"
    SYSTEM = "system"


class LogSourceKind(StrEnum):
    CORE = "core"
    ENGINE = "engine"
    PLUGIN = "plugin"
    THEME = "theme"


@dataclass(frozen=True)
class LogSource:
    kind: LogSourceKind
    identifier: str

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("Log source identifier must not be empty")


@dataclass(frozen=True)
class LogRecord:
    timestamp: str
    log_id: str
    level: LogLevel
    category: LogCategory
    source: LogSource
    message: str
    context: Mapping[str, object]


class LogOutput(Protocol):
    def emit(self, record: LogRecord) -> None: ...


class MemoryLogOutput:
    def __init__(self) -> None:
        self.records: list[LogRecord] = []

    def emit(self, record: LogRecord) -> None:
        self.records.append(record)


class JsonConsoleOutput:
    def emit(self, record: LogRecord) -> None:
        payload = asdict(record)
        payload["level"] = record.level.name.lower()
        print(json.dumps(payload, separators=(",", ":"), default=str), flush=True)


_ALLOWED_CONTEXT_KEYS = frozenset(
    {
        "request_id",
        "route_id",
        "component_id",
        "engine_id",
        "plugin_id",
        "job_id",
        "operation_id",
        "error_id",
        "correlation_id",
        "exception_type",
    }
)
_SENSITIVE_FRAGMENTS = (
    "password",
    "credential",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "database_url",
)
_REDACTED = "[REDACTED]"


class LoggingEngine:
    def __init__(
        self,
        *,
        outputs: tuple[LogOutput, ...] = (),
        minimum_level: LogLevel = LogLevel.INFO,
        enabled_categories: frozenset[LogCategory] | None = None,
        enabled_sources: frozenset[str] | None = None,
    ) -> None:
        self._outputs = outputs
        self._minimum_level = minimum_level
        self._enabled_categories = enabled_categories
        self._enabled_sources = enabled_sources

    def log(
        self,
        level: LogLevel,
        message: str,
        *,
        source: LogSource,
        category: LogCategory,
        context: Mapping[str, object] | None = None,
    ) -> LogRecord | None:
        if level < self._minimum_level:
            return None
        if self._enabled_categories is not None and category not in self._enabled_categories:
            return None
        if self._enabled_sources is not None and source.identifier not in self._enabled_sources:
            return None

        safe_context = _sanitize_context(context or {})
        record = LogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            log_id=str(uuid4()),
            level=level,
            category=category,
            source=source,
            message=_sanitize_message(message),
            context=MappingProxyType(safe_context),
        )
        for output in self._outputs:
            try:
                output.emit(record)
            except Exception:
                # Logging is operational support and cannot replace the primary outcome.
                continue
        return record

    def debug(self, message: str, *, source: LogSource, category: LogCategory,
              context: Mapping[str, object] | None = None) -> LogRecord | None:
        return self.log(LogLevel.DEBUG, message, source=source, category=category, context=context)

    def info(self, message: str, *, source: LogSource, category: LogCategory,
             context: Mapping[str, object] | None = None) -> LogRecord | None:
        return self.log(LogLevel.INFO, message, source=source, category=category, context=context)

    def warning(self, message: str, *, source: LogSource, category: LogCategory,
                context: Mapping[str, object] | None = None) -> LogRecord | None:
        return self.log(LogLevel.WARNING, message, source=source, category=category, context=context)

    def error(self, message: str, *, source: LogSource, category: LogCategory,
              context: Mapping[str, object] | None = None) -> LogRecord | None:
        return self.log(LogLevel.ERROR, message, source=source, category=category, context=context)

    def exception(self, error: BaseException, *, source: LogSource, category: LogCategory,
                  context: Mapping[str, object] | None = None) -> LogRecord | None:
        safe_context = dict(context or {})
        safe_context["exception_type"] = type(error).__name__
        return self.error(
            "An operation failed",
            source=source,
            category=category,
            context=safe_context,
        )


def _sanitize_context(context: Mapping[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in context.items():
        normalized = key.strip().lower()
        if normalized not in _ALLOWED_CONTEXT_KEYS:
            continue
        if any(fragment in normalized for fragment in _SENSITIVE_FRAGMENTS):
            safe[normalized] = _REDACTED
        elif isinstance(value, (str, int, float, bool)) or value is None:
            safe[normalized] = value
    return safe


def _sanitize_message(message: str) -> str:
    lowered = message.lower()
    if any(fragment in lowered for fragment in _SENSITIVE_FRAGMENTS):
        return "Sensitive operational message redacted"
    return message

