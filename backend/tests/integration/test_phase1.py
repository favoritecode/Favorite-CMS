import pytest

from backend.bootstrap import build_kernel
from backend.config import Configuration
from backend.core.contracts.engine import EngineLifecycle
from backend.core.engine_manager import EngineManager
from backend.core.exceptions import EngineLifecycleError
from backend.core.extensions import ExtensionManager
from backend.engines.errors import ErrorHandlingEngine
from backend.engines.logging import LoggingEngine


def test_phase1_bootstrap_registers_only_public_runtime_contracts() -> None:
    kernel = build_kernel()
    kernel.bootstrap()
    assert kernel.ready
    assert kernel.container.resolve("core.configuration", Configuration) is kernel.configuration
    assert kernel.container.resolve("core.logging", LoggingEngine) is kernel.logging
    assert kernel.container.resolve("core.errors", ErrorHandlingEngine) is kernel.errors
    assert kernel.container.resolve("core.extensions", ExtensionManager) is kernel.extensions
    kernel.shutdown()
    assert not kernel.ready


def test_phase1_contains_no_future_engine_registrations() -> None:
    kernel = build_kernel()
    kernel.bootstrap()
    forbidden = (
        "settings", "authentication", "permission", "routing", "api", "rendering",
    )
    assert all(not kernel.container.contains(f"core.{name}") for name in forbidden)


def test_kernel_records_startup_failure_and_does_not_become_ready() -> None:
    class FailingEngine:
        engine_id = "failing"
        dependencies: tuple[str, ...] = ()

        def initialize(self, container: object) -> None:
            pass

        def start(self) -> None:
            raise RuntimeError("secret=must-not-leak")

        def shutdown(self) -> None:
            pass

    manager = EngineManager()
    manager.register(FailingEngine())
    kernel = build_kernel()
    kernel.engines = manager
    with pytest.raises(EngineLifecycleError):
        kernel.bootstrap()
    assert not kernel.ready
    assert kernel.failure is not None
    assert kernel.failure.safe_message == "An internal error occurred"
    assert manager.state("failing") is EngineLifecycle.FAILED
