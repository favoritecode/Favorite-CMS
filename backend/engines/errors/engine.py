"""Safe failure normalization without business recovery policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping
from uuid import uuid4


class ErrorCategory(StrEnum):
    VALIDATION = "validation"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    INTERNAL = "internal"


class ErrorSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ApplicationFailure(Exception):
    category = ErrorCategory.APPLICATION
    severity = ErrorSeverity.ERROR

    def __init__(self, safe_message: str, *, context: Mapping[str, object] | None = None) -> None:
        super().__init__(safe_message)
        self.safe_message = safe_message
        self.context = context or {}


class ValidationFailure(ApplicationFailure):
    category = ErrorCategory.VALIDATION
    severity = ErrorSeverity.WARNING


class InfrastructureFailure(ApplicationFailure):
    category = ErrorCategory.INFRASTRUCTURE
    severity = ErrorSeverity.CRITICAL


@dataclass(frozen=True)
class PublicError:
    error_id: str
    category: ErrorCategory
    message: str


@dataclass(frozen=True)
class ErrorRecord:
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    source: str
    safe_message: str
    context: Mapping[str, object]
    diagnostic_type: str

    def public(self) -> PublicError:
        return PublicError(self.error_id, self.category, self.safe_message)


_SAFE_CONTEXT_KEYS = frozenset(
    {"request_id", "route_id", "engine_id", "plugin_id", "job_id", "operation_id"}
)


class ErrorHandlingEngine:
    def normalize(
        self,
        error: BaseException,
        *,
        source: str,
        context: Mapping[str, object] | None = None,
    ) -> ErrorRecord:
        try:
            if not source.strip():
                raise ValueError("Error source must not be empty")
            if isinstance(error, ApplicationFailure):
                category = error.category
                severity = error.severity
                message = _safe_message(error.safe_message)
                merged = {**error.context, **(context or {})}
            else:
                category = ErrorCategory.INTERNAL
                severity = ErrorSeverity.CRITICAL
                message = "An internal error occurred"
                merged = context or {}
            safe_context = {
                key: value
                for key, value in merged.items()
                if key in _SAFE_CONTEXT_KEYS
                and (isinstance(value, (str, int, float, bool)) or value is None)
            }
            return ErrorRecord(
                error_id=str(uuid4()),
                category=category,
                severity=severity,
                source=source,
                safe_message=message,
                context=MappingProxyType(safe_context),
                diagnostic_type=type(error).__name__,
            )
        except Exception:
            return ErrorRecord(
                error_id=str(uuid4()),
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.CRITICAL,
                source="error-handling",
                safe_message="An internal error occurred",
                context=MappingProxyType({}),
                diagnostic_type="NormalizationFailure",
            )


def _safe_message(message: str) -> str:
    sensitive = ("password", "credential", "token", "secret", "database_url", "file://", "\\")
    if any(fragment in message.lower() for fragment in sensitive):
        return "The operation could not be completed"
    return message

