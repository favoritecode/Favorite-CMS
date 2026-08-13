import pytest

from backend.core.container import ServiceContainer
from backend.engines.errors import ErrorHandlingEngine
from backend.engines.events import EventContract, EventEngine, EventError
from backend.engines.logging import LoggingEngine, MemoryLogOutput


def started_events(output: MemoryLogOutput | None = None) -> EventEngine:
    container = ServiceContainer()
    container.register("core.errors", ErrorHandlingEngine())
    container.register("core.logging", LoggingEngine(outputs=(output,) if output else ()))
    events = EventEngine()
    events.initialize(container)
    events.start()
    return events


def contract() -> EventContract:
    def validate(payload: dict[str, object]) -> None:
        if "resource_id" not in payload:
            raise ValueError("resource_id required")
    return EventContract("test.resource.changed", "test.publisher", validate)


def test_event_creation_identity_payload_and_dispatch_order() -> None:
    events = started_events()
    events.register(contract())
    calls: list[str] = []
    events.subscribe("test.resource.changed", "first", lambda event: calls.append("first"))
    events.subscribe("test.resource.changed", "second", lambda event: calls.append("second"))
    event = events.create("test.resource.changed", "test.publisher", {"resource_id": "r1"})
    result = events.publish(event)
    assert event.event_id and event.payload == {"resource_id": "r1"}
    assert result.delivered == 2
    assert calls == ["first", "second"]


def test_invalid_event_contract_payload_and_publisher_are_rejected() -> None:
    events = started_events()
    events.register(contract())
    with pytest.raises(ValueError):
        events.create("test.resource.changed", "test.publisher", {})
    with pytest.raises(EventError, match="publisher"):
        events.create("test.resource.changed", "other", {"resource_id": "r1"})
    with pytest.raises(EventError, match="prohibited"):
        events.create(
            "test.resource.changed", "test.publisher", {"resource_id": "r1", "access_token": "x"}
        )


def test_failing_handler_is_isolated_and_logged() -> None:
    output = MemoryLogOutput()
    events = started_events(output)
    events.register(contract())
    calls: list[str] = []
    events.subscribe("test.resource.changed", "broken", lambda event: (_ for _ in ()).throw(RuntimeError("secret")))
    events.subscribe("test.resource.changed", "healthy", lambda event: calls.append("healthy"))
    result = events.publish(
        events.create("test.resource.changed", "test.publisher", {"resource_id": "r1"})
    )
    assert result.delivered == 1
    assert len(result.failures) == 1
    assert calls == ["healthy"]
    assert output.records and "secret" not in repr(output.records)


def test_nested_synchronous_publish_is_blocked_without_stopping_other_listener() -> None:
    events = started_events()
    events.register(contract())
    event = events.create("test.resource.changed", "test.publisher", {"resource_id": "r1"})
    events.subscribe("test.resource.changed", "recursive", lambda received: events.publish(event))
    events.subscribe("test.resource.changed", "healthy", lambda received: None)
    result = events.publish(event)
    assert result.delivered == 1
    assert len(result.failures) == 1


def test_event_lifecycle_stops_publication() -> None:
    events = started_events()
    events.register(contract())
    event = events.create("test.resource.changed", "test.publisher", {"resource_id": "r1"})
    events.shutdown()
    with pytest.raises(EventError, match="unavailable"):
        events.publish(event)

