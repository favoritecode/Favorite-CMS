"""Generic notification coordination and provider-neutral delivery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import re
from types import MappingProxyType
from typing import Callable, Mapping, Protocol
from uuid import uuid4

from backend.core.container import ServiceContainer
from backend.engines.errors import ErrorHandlingEngine, ErrorRecord
from backend.engines.logging import LogCategory, LogSource, LogSourceKind, LoggingEngine
from backend.engines.queue import Job, JobContract, JobResult, QueueEngine, RetryPolicy
from backend.engines.settings import (SettingDefinition, SettingScope, SettingScopeKind,
                                      SettingsEngine)


class NotificationError(ValueError):
    pass


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


_TYPE = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$")
_CHANNEL = re.compile(r"^[a-z][a-z0-9-]*$")
_SENSITIVE = ("password", "credential", "token", "secret", "authorization", "cookie")
PayloadValidator = Callable[[Mapping[str, object]], None]
RecipientValidator = Callable[["NotificationRecipient"], None]


@dataclass(frozen=True)
class NotificationRecipient:
    recipient_id: str
    scope: str
    destination: str

    def __post_init__(self) -> None:
        if not self.recipient_id.strip() or not self.scope.strip() or not self.destination.strip():
            raise NotificationError("Notification Recipient is incomplete")


@dataclass(frozen=True)
class NotificationContract:
    notification_type: str
    producer: str
    validate_payload: PayloadValidator
    validate_recipient: RecipientValidator
    channels: frozenset[str]

    def __post_init__(self) -> None:
        if not _TYPE.fullmatch(self.notification_type) or not self.producer.strip():
            raise NotificationError("Notification contract identity is invalid")
        if not self.channels or any(not _CHANNEL.fullmatch(item) for item in self.channels):
            raise NotificationError("Notification channels are invalid")


@dataclass
class Notification:
    notification_id: str
    notification_type: str
    producer: str
    recipient: NotificationRecipient
    channel: str
    payload: Mapping[str, object]
    created_at: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    failure: ErrorRecord | None = None


@dataclass(frozen=True)
class DeliveryResult:
    notification_id: str
    status: DeliveryStatus
    attempts: int
    failure: ErrorRecord | None = None


@dataclass(frozen=True)
class DeliverySummary:
    notification_type: str
    pending: int
    delivered: int
    failed: int
    attempts: int
    provider_available: bool


class DeliveryAdapter(Protocol):
    channel: str
    def deliver(self, notification: Notification) -> None: ...
    def healthcheck(self) -> bool: ...


class MemoryDeliveryAdapter:
    """Development/test adapter that records normalized Notification objects."""

    def __init__(self, channel: str = "in-app") -> None:
        if not _CHANNEL.fullmatch(channel):
            raise NotificationError("Notification channel is invalid")
        self.channel = channel
        self.delivered: list[Notification] = []

    def deliver(self, notification: Notification) -> None:
        self.delivered.append(notification)

    def healthcheck(self) -> bool:
        return True


class NotificationEngine:
    engine_id = "notifications"
    dependencies = ("settings",)

    def __init__(self) -> None:
        self._contracts: dict[str, NotificationContract] = {}
        self._adapters: dict[str, DeliveryAdapter] = {}
        self._notifications: dict[str, Notification] = {}
        self._errors: ErrorHandlingEngine | None = None
        self._logging: LoggingEngine | None = None
        self._settings: SettingsEngine | None = None
        self._hydrated = False
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._errors = container.resolve("core.errors", ErrorHandlingEngine)
        self._logging = container.resolve("core.logging", LoggingEngine)
        if container.contains("engine.settings"):
            self._settings = container.resolve("engine.settings", SettingsEngine)
            self._settings.register(SettingDefinition(
                "delivery_requests", "engine.notifications", SettingScopeKind.ENGINE,
                list, default=[], validator=_validate_stored_notifications,
            ))
        container.register("engine.notifications", self)

    def start(self) -> None:
        self.ready = True

    def shutdown(self) -> None:
        self._notifications.clear()
        self._hydrated = False
        self.ready = False

    def register_contract(self, contract: NotificationContract) -> None:
        if contract.notification_type in self._contracts:
            raise NotificationError(
                f"Notification contract is already registered: {contract.notification_type}"
            )
        self._contracts[contract.notification_type] = contract

    def unregister_contract(self, notification_type: str, *, producer: str) -> None:
        """Remove only the caller-owned contract during deterministic Plugin cleanup."""
        contract = self._contract(notification_type)
        if contract.producer != producer:
            raise NotificationError("Notification producer is not approved")
        self._contracts.pop(notification_type)

    def register_adapter(self, adapter: DeliveryAdapter) -> None:
        if adapter.channel in self._adapters:
            raise NotificationError(f"Delivery channel is already registered: {adapter.channel}")
        if not adapter.healthcheck():
            raise NotificationError("Delivery Adapter is unavailable")
        self._adapters[adapter.channel] = adapter

    def create(
        self,
        notification_type: str,
        producer: str,
        recipient: NotificationRecipient,
        channel: str,
        payload: Mapping[str, object],
    ) -> DeliveryResult:
        if not self.ready:
            raise NotificationError("Notification Engine is unavailable")
        self._ensure_hydrated()
        contract = self._contract(notification_type)
        if producer != contract.producer:
            raise NotificationError("Notification producer is not approved")
        if channel not in contract.channels:
            raise NotificationError("Notification channel is unsupported")
        safe_payload = _validate_payload(payload)
        contract.validate_payload(safe_payload)
        contract.validate_recipient(recipient)
        notification = Notification(
            notification_id=str(uuid4()),
            notification_type=notification_type,
            producer=producer,
            recipient=recipient,
            channel=channel,
            payload=MappingProxyType(dict(safe_payload)),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._notifications[notification.notification_id] = notification
        self._persist()
        return self.result(notification.notification_id)

    def adapter_available(self, channel: str) -> bool:
        """Expose provider availability without exposing adapter configuration or secrets."""
        return channel in self._adapters

    def operational_status(self) -> Mapping[str, object]:
        """Return aggregate delivery health without recipients, payloads, or adapter details."""
        self._ensure_hydrated()
        counts = {status.value: 0 for status in DeliveryStatus}
        attempts = 0
        for notification in self._notifications.values():
            counts[notification.status.value] += 1
            attempts += notification.attempts
        return MappingProxyType({
            "status": "healthy" if self.ready and self._adapters else "not_configured" if self.ready else "unavailable",
            "provider_configured": bool(self._adapters),
            "pending": counts[DeliveryStatus.PENDING.value],
            "delivered": counts[DeliveryStatus.DELIVERED.value],
            "failed": counts[DeliveryStatus.FAILED.value],
            "attempts": attempts,
        })

    def deliver(self, notification_id: str) -> DeliveryResult:
        notification = self._notification(notification_id)
        if notification.status is DeliveryStatus.DELIVERED:
            return self.result(notification_id)
        if notification.channel not in self._adapters:
            return self.result(notification_id)
        notification.attempts += 1
        try:
            adapter = self._adapters[notification.channel]
            adapter.deliver(notification)
            notification.status = DeliveryStatus.DELIVERED
            notification.failure = None
        except Exception as exc:
            failure = self._require_errors().normalize(
                exc,
                source=f"notification-adapter:{notification.channel}",
                context={"operation_id": notification.notification_id},
            )
            notification.status = DeliveryStatus.FAILED
            notification.failure = failure
            self._log_failure(failure)
        self._persist()
        return self.result(notification_id)

    def register_deferred_delivery(
        self,
        queue: QueueEngine,
        job_type: str,
        *,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Register an explicitly named Queue contract for deferred delivery."""
        def validate(payload: Mapping[str, object]) -> None:
            notification_id = payload.get("notification_id")
            if not isinstance(notification_id, str) or notification_id not in self._notifications:
                raise NotificationError("Deferred Notification reference is invalid")

        def handle(job: Job) -> DeliveryResult:
            result = self.deliver(str(job.payload["notification_id"]))
            if result.status is DeliveryStatus.FAILED:
                raise NotificationError("Deferred Notification delivery failed")
            return result

        queue.register(
            JobContract(
                job_type=job_type,
                producer="engine.notifications",
                validate_payload=validate,
                handler=handle,
                retry=retry,
            )
        )

    def defer(self, notification_id: str, queue: QueueEngine, job_type: str) -> JobResult:
        notification = self._notification(notification_id)
        if notification.status is not DeliveryStatus.PENDING:
            raise NotificationError("Only pending Notifications may be deferred")
        return queue.submit(
            job_type,
            "engine.notifications",
            {"notification_id": notification_id},
        )

    def result(self, notification_id: str) -> DeliveryResult:
        self._ensure_hydrated()
        notification = self._notification(notification_id)
        return DeliveryResult(
            notification.notification_id,
            notification.status,
            notification.attempts,
            notification.failure,
        )

    def for_recipient(self, recipient_id: str, scope: str) -> tuple[Notification, ...]:
        self._ensure_hydrated()
        return tuple(
            item
            for item in self._notifications.values()
            if item.recipient.recipient_id == recipient_id and item.recipient.scope == scope
        )

    def delivery_summary(self, notification_type: str, *, producer: str) -> DeliverySummary:
        """Return operational counts without recipient, payload, adapter, or failure details."""
        self._ensure_hydrated()
        contract = self._contract(notification_type)
        if contract.producer != producer:
            raise NotificationError("Notification producer is not approved")
        items = tuple(item for item in self._notifications.values()
                      if item.notification_type == notification_type and item.producer == producer)
        return DeliverySummary(
            notification_type,
            sum(item.status is DeliveryStatus.PENDING for item in items),
            sum(item.status is DeliveryStatus.DELIVERED for item in items),
            sum(item.status is DeliveryStatus.FAILED for item in items),
            sum(item.attempts for item in items),
            any(self.adapter_available(channel) for channel in contract.channels),
        )

    def _contract(self, notification_type: str) -> NotificationContract:
        try:
            return self._contracts[notification_type]
        except KeyError as exc:
            raise NotificationError("Notification contract is not registered") from exc

    def _notification(self, notification_id: str) -> Notification:
        self._ensure_hydrated()
        try:
            return self._notifications[notification_id]
        except KeyError as exc:
            raise NotificationError("Notification is not registered") from exc

    def _ensure_hydrated(self) -> None:
        if self._hydrated:
            return
        if self._settings is None:
            self._hydrated = True
            return
        value = self._settings.get("delivery_requests", _notification_scope()).value
        if not isinstance(value, list):
            raise NotificationError("Stored Notification state is invalid")
        restored: dict[str, Notification] = {}
        for item in value:
            recipient = NotificationRecipient(str(item["recipient_id"]), str(item["recipient_scope"]),
                                              str(item["destination"]))
            notification = Notification(
                str(item["notification_id"]), str(item["notification_type"]), str(item["producer"]),
                recipient, str(item["channel"]), MappingProxyType(dict(item["payload"])),
                str(item["created_at"]), DeliveryStatus(str(item["status"])), int(item["attempts"]), None,
            )
            restored[notification.notification_id] = notification
        self._notifications = restored
        self._hydrated = True

    def _persist(self) -> None:
        if self._settings is None:
            return
        values = [_stored_notification(item) for item in self._notifications.values()]
        self._settings.set("delivery_requests", _notification_scope(), values[-500:])

    def _require_errors(self) -> ErrorHandlingEngine:
        if self._errors is None:
            raise NotificationError("Notification Engine is not initialized")
        return self._errors

    def _log_failure(self, error: ErrorRecord) -> None:
        if self._logging is not None:
            self._logging.error(
                "Notification delivery failed",
                source=LogSource(LogSourceKind.ENGINE, "notifications"),
                category=LogCategory.ENGINE,
                context={"error_id": error.error_id, "operation_id": error.context.get("operation_id")},
            )


def _validate_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise NotificationError("Notification Payload must be structured data")
    for key in payload:
        if not isinstance(key, str) or any(fragment in key.lower() for fragment in _SENSITIVE):
            raise NotificationError("Notification Payload contains a prohibited field")
    return payload


def _notification_scope() -> SettingScope:
    return SettingScope(SettingScopeKind.ENGINE, "engine.notifications")


def _stored_notification(item: Notification) -> dict[str, object]:
    return {
        "notification_id": item.notification_id, "notification_type": item.notification_type,
        "producer": item.producer, "recipient_id": item.recipient.recipient_id,
        "recipient_scope": item.recipient.scope, "destination": item.recipient.destination,
        "channel": item.channel, "payload": dict(item.payload), "created_at": item.created_at,
        "status": item.status.value, "attempts": item.attempts,
    }


def _validate_stored_notifications(value: object) -> None:
    fields = {"notification_id", "notification_type", "producer", "recipient_id", "recipient_scope",
              "destination", "channel", "payload", "created_at", "status", "attempts"}
    if not isinstance(value, list) or len(value) > 500:
        raise NotificationError("Stored Notification state is invalid")
    for item in value:
        if (not isinstance(item, dict) or set(item) != fields
                or any(not isinstance(item[key], str) for key in fields - {"payload", "attempts"})
                or not isinstance(item["payload"], dict) or not isinstance(item["attempts"], int)
                or item["attempts"] < 0 or item["status"] not in {status.value for status in DeliveryStatus}):
            raise NotificationError("Stored Notification state is invalid")
        _validate_payload(item["payload"])
