import pytest

from backend.core.container import ServiceContainer
from backend.engines.errors import ErrorHandlingEngine
from backend.engines.logging import LoggingEngine, MemoryLogOutput
from backend.engines.notifications import (
    DeliveryStatus,
    MemoryDeliveryAdapter,
    NotificationContract,
    NotificationEngine,
    NotificationError,
    NotificationRecipient,
)
from backend.engines.queue import JobStatus, QueueEngine


def started_notifications(output: MemoryLogOutput | None = None) -> NotificationEngine:
    container = ServiceContainer()
    container.register("core.errors", ErrorHandlingEngine())
    container.register("core.logging", LoggingEngine(outputs=(output,) if output else ()))
    notifications = NotificationEngine()
    notifications.initialize(container)
    notifications.start()
    return notifications


def contract() -> NotificationContract:
    def validate_payload(payload: dict[str, object]) -> None:
        if "message" not in payload:
            raise ValueError("message required")
    def validate_recipient(recipient: NotificationRecipient) -> None:
        if recipient.scope != "test":
            raise ValueError("scope invalid")
    return NotificationContract(
        "test.notification.message", "test.producer", validate_payload,
        validate_recipient, frozenset({"in-app"}),
    )


def test_create_resolve_channel_deliver_and_record_status() -> None:
    notifications = started_notifications()
    adapter = MemoryDeliveryAdapter()
    notifications.register_adapter(adapter)
    notifications.register_contract(contract())
    recipient = NotificationRecipient("recipient-1", "test", "destination-1")
    created = notifications.create(
        "test.notification.message", "test.producer", recipient, "in-app", {"message": "Hello"}
    )
    assert created.status is DeliveryStatus.PENDING
    delivered = notifications.deliver(created.notification_id)
    assert delivered.status is DeliveryStatus.DELIVERED and delivered.attempts == 1
    assert len(adapter.delivered) == 1


def test_invalid_recipient_channel_payload_and_producer_are_rejected() -> None:
    notifications = started_notifications()
    notifications.register_adapter(MemoryDeliveryAdapter())
    notifications.register_contract(contract())
    recipient = NotificationRecipient("recipient-1", "test", "destination")
    with pytest.raises(NotificationError, match="producer"):
        notifications.create("test.notification.message", "other", recipient, "in-app", {"message": "x"})
    with pytest.raises(NotificationError, match="unsupported"):
        notifications.create("test.notification.message", "test.producer", recipient, "email", {"message": "x"})
    with pytest.raises(NotificationError, match="prohibited"):
        notifications.create(
            "test.notification.message", "test.producer", recipient, "in-app",
            {"message": "x", "access_token": "secret"},
        )


def test_provider_failure_is_controlled_logged_and_not_delivered() -> None:
    class BrokenAdapter:
        channel = "in-app"
        def healthcheck(self) -> bool: return True
        def deliver(self, notification: object) -> None: raise RuntimeError("provider credential")

    output = MemoryLogOutput()
    notifications = started_notifications(output)
    notifications.register_adapter(BrokenAdapter())
    notifications.register_contract(contract())
    created = notifications.create(
        "test.notification.message", "test.producer",
        NotificationRecipient("recipient-1", "test", "destination"),
        "in-app", {"message": "Hello"},
    )
    failed = notifications.deliver(created.notification_id)
    assert failed.status is DeliveryStatus.FAILED and failed.attempts == 1
    assert "provider credential" not in repr(failed.failure.public())  # type: ignore[union-attr]
    assert output.records and "provider credential" not in repr(output.records)


def test_recipient_query_is_isolated_by_identity_and_scope() -> None:
    notifications = started_notifications()
    notifications.register_adapter(MemoryDeliveryAdapter())
    notifications.register_contract(contract())
    first = NotificationRecipient("one", "test", "destination-one")
    second = NotificationRecipient("two", "test", "destination-two")
    notifications.create("test.notification.message", "test.producer", first, "in-app", {"message": "one"})
    notifications.create("test.notification.message", "test.producer", second, "in-app", {"message": "two"})
    result = notifications.for_recipient("one", "test")
    assert len(result) == 1 and result[0].recipient == first


def test_delivery_is_idempotent_after_success_and_shutdown_is_clean() -> None:
    notifications = started_notifications()
    adapter = MemoryDeliveryAdapter()
    notifications.register_adapter(adapter)
    notifications.register_contract(contract())
    created = notifications.create(
        "test.notification.message", "test.producer",
        NotificationRecipient("one", "test", "destination"), "in-app", {"message": "one"},
    )
    notifications.deliver(created.notification_id)
    notifications.deliver(created.notification_id)
    assert len(adapter.delivered) == 1
    notifications.shutdown()
    assert not notifications.ready


def test_deferred_delivery_uses_queue_while_notification_owns_state() -> None:
    notifications = started_notifications()
    adapter = MemoryDeliveryAdapter()
    notifications.register_adapter(adapter)
    notifications.register_contract(contract())
    container = ServiceContainer()
    container.register("core.errors", ErrorHandlingEngine())
    container.register("core.logging", LoggingEngine())
    queue = QueueEngine()
    queue.initialize(container)
    queue.start()
    notifications.register_deferred_delivery(queue, "test.notification.delivery")
    created = notifications.create(
        "test.notification.message", "test.producer",
        NotificationRecipient("one", "test", "destination"), "in-app", {"message": "one"},
    )
    queued = notifications.defer(created.notification_id, queue, "test.notification.delivery")
    assert queued.status is JobStatus.PENDING
    assert notifications.result(created.notification_id).status is DeliveryStatus.PENDING
    queue.process_next()
    assert notifications.result(created.notification_id).status is DeliveryStatus.DELIVERED
    assert len(adapter.delivered) == 1
