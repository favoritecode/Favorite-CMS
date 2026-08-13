"""Validated synchronous event delivery with listener isolation.

The implementation guarantees subscription registration order only. It does
not provide persistence, retries, asynchronous delivery, or global ordering.
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from types import MappingProxyType
from typing import Callable, Mapping
from uuid import uuid4

from backend.core.container import ServiceContainer
from backend.engines.errors import ErrorHandlingEngine, ErrorRecord
from backend.engines.logging import LogCategory, LogSource, LogSourceKind, LoggingEngine


class EventError(ValueError):
    pass


PayloadValidator = Callable[[Mapping[str, object]], None]
EventListener = Callable[["Event"], None]
_NAME = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$")
_SENSITIVE = ("password", "credential", "token", "secret", "authorization", "cookie")
_dispatch_active: ContextVar[bool] = ContextVar("favorite_event_dispatch_active", default=False)


@dataclass(frozen=True)
class EventContract:
    name: str
    publisher: str
    validate_payload: PayloadValidator

    def __post_init__(self) -> None:
        if not _NAME.fullmatch(self.name) or not self.publisher.strip():
            raise EventError("Event contract identity is invalid")


@dataclass(frozen=True)
class Event:
    event_id: str
    name: str
    publisher: str
    payload: Mapping[str, object]
    occurred_at: str
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ListenerFailure:
    subscriber: str
    error: ErrorRecord


@dataclass(frozen=True)
class EventDispatchResult:
    event_id: str
    delivered: int
    failures: tuple[ListenerFailure, ...]


@dataclass(frozen=True)
class _Subscription:
    subscriber: str
    listener: EventListener


class EventEngine:
    engine_id = "events"
    dependencies: tuple[str, ...] = ()

    def __init__(self) -> None:
        self._contracts: dict[str, EventContract] = {}
        self._subscriptions: dict[str, list[_Subscription]] = {}
        self._errors: ErrorHandlingEngine | None = None
        self._logging: LoggingEngine | None = None
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._errors = container.resolve("core.errors", ErrorHandlingEngine)
        self._logging = container.resolve("core.logging", LoggingEngine)
        container.register("engine.events", self)

    def start(self) -> None:
        self.ready = True

    def shutdown(self) -> None:
        self.ready = False

    def register(self, contract: EventContract) -> None:
        if contract.name in self._contracts:
            raise EventError(f"Event contract is already registered: {contract.name}")
        self._contracts[contract.name] = contract

    def subscribe(self, name: str, subscriber: str, listener: EventListener) -> None:
        if name not in self._contracts:
            raise EventError(f"Event contract is not registered: {name}")
        if not subscriber.strip() or not callable(listener):
            raise EventError("Event subscription is invalid")
        self._subscriptions.setdefault(name, []).append(_Subscription(subscriber, listener))

    def unsubscribe(self, name: str, subscriber: str) -> None:
        subscriptions = self._subscriptions.get(name, [])
        self._subscriptions[name] = [item for item in subscriptions if item.subscriber != subscriber]

    def create(
        self,
        name: str,
        publisher: str,
        payload: Mapping[str, object],
        *,
        metadata: Mapping[str, object] | None = None,
    ) -> Event:
        contract = self._contract(name)
        if publisher != contract.publisher:
            raise EventError("Event publisher is not approved for this contract")
        safe_payload = _validate_mapping(payload, "Event Payload")
        safe_metadata = _validate_mapping(metadata or {}, "Event metadata")
        contract.validate_payload(safe_payload)
        return Event(
            event_id=str(uuid4()),
            name=name,
            publisher=publisher,
            payload=MappingProxyType(dict(safe_payload)),
            occurred_at=datetime.now(timezone.utc).isoformat(),
            metadata=MappingProxyType(dict(safe_metadata)),
        )

    def publish(self, event: Event) -> EventDispatchResult:
        if not self.ready:
            raise EventError("Event Engine is unavailable")
        if _dispatch_active.get():
            raise EventError("Nested synchronous Event publication is not supported")
        contract = self._contract(event.name)
        if event.publisher != contract.publisher:
            raise EventError("Event publisher is not approved for this contract")
        contract.validate_payload(_validate_mapping(event.payload, "Event Payload"))
        token = _dispatch_active.set(True)
        delivered = 0
        failures: list[ListenerFailure] = []
        try:
            for subscription in tuple(self._subscriptions.get(event.name, ())):
                try:
                    subscription.listener(event)
                    delivered += 1
                except Exception as exc:
                    error = self._require_errors().normalize(
                        exc,
                        source=f"event-consumer:{subscription.subscriber}",
                        context={"operation_id": event.event_id},
                    )
                    failures.append(ListenerFailure(subscription.subscriber, error))
                    self._log_failure(error)
        finally:
            _dispatch_active.reset(token)
        return EventDispatchResult(event.event_id, delivered, tuple(failures))

    def _contract(self, name: str) -> EventContract:
        try:
            return self._contracts[name]
        except KeyError as exc:
            raise EventError(f"Event contract is not registered: {name}") from exc

    def _require_errors(self) -> ErrorHandlingEngine:
        if self._errors is None:
            raise EventError("Event Engine is not initialized")
        return self._errors

    def _log_failure(self, error: ErrorRecord) -> None:
        if self._logging is not None:
            self._logging.error(
                "Event consumer failed",
                source=LogSource(LogSourceKind.ENGINE, "events"),
                category=LogCategory.ENGINE,
                context={"error_id": error.error_id, "operation_id": error.context.get("operation_id")},
            )


def _validate_mapping(value: Mapping[str, object], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise EventError(f"{label} must be structured data")
    for key in value:
        if not isinstance(key, str) or any(fragment in key.lower() for fragment in _SENSITIVE):
            raise EventError(f"{label} contains a prohibited field")
    return value

