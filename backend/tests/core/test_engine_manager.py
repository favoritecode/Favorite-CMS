from dataclasses import dataclass, field

import pytest

from backend.core.container import ServiceContainer
from backend.core.contracts.engine import EngineLifecycle
from backend.core.engine_manager import EngineManager
from backend.core.exceptions import EngineLifecycleError


@dataclass
class FakeEngine:
    engine_id: str
    dependencies: tuple[str, ...] = ()
    fail_start: bool = False
    calls: list[str] = field(default_factory=list)

    def initialize(self, container: ServiceContainer) -> None:
        self.calls.append("initialize")

    def start(self) -> None:
        self.calls.append("start")
        if self.fail_start:
            raise RuntimeError("failed")

    def shutdown(self) -> None:
        self.calls.append("shutdown")


def test_lifecycle_is_dependency_ordered_and_shutdown_is_reversed() -> None:
    manager = EngineManager()
    dependent = FakeEngine("b", ("a",))
    dependency = FakeEngine("a")
    manager.register(dependent)
    manager.register(dependency)
    manager.initialize_and_start(ServiceContainer())
    assert manager.state("a") is EngineLifecycle.STARTED
    assert manager.state("b") is EngineLifecycle.STARTED
    manager.shutdown()
    assert dependency.calls == ["initialize", "start", "shutdown"]
    assert dependent.calls == ["initialize", "start", "shutdown"]


def test_start_failure_stops_engines_already_started() -> None:
    manager = EngineManager()
    first = FakeEngine("a")
    failing = FakeEngine("b", ("a",), fail_start=True)
    manager.register(first)
    manager.register(failing)
    with pytest.raises(EngineLifecycleError, match="b"):
        manager.initialize_and_start(ServiceContainer())
    assert manager.state("a") is EngineLifecycle.STOPPED
    assert manager.state("b") is EngineLifecycle.FAILED


def test_missing_engine_dependency_fails_before_startup() -> None:
    manager = EngineManager()
    manager.register(FakeEngine("dependent", ("missing",)))
    with pytest.raises(EngineLifecycleError, match="missing"):
        manager.initialize_and_start(ServiceContainer())

