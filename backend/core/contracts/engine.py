from __future__ import annotations

from enum import Enum
from typing import Protocol

from backend.core.container import ServiceContainer


class EngineLifecycle(str, Enum):
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    STARTED = "started"
    FAILED = "failed"
    STOPPED = "stopped"


class Engine(Protocol):
    engine_id: str
    dependencies: tuple[str, ...]

    def initialize(self, container: ServiceContainer) -> None: ...
    def start(self) -> None: ...
    def shutdown(self) -> None: ...

