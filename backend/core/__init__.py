"""Stable, business-neutral Core boundary."""

from backend.core.container import ServiceContainer
from backend.core.engine_manager import EngineManager
from backend.core.kernel import Kernel

__all__ = ["EngineManager", "Kernel", "ServiceContainer"]
