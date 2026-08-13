"""Deterministic lifecycle coordinator for built-in Engine contracts."""

from __future__ import annotations

from collections.abc import Iterable

from backend.core.container import ServiceContainer
from backend.core.contracts.engine import Engine, EngineLifecycle
from backend.core.exceptions import EngineLifecycleError


class EngineManager:
    def __init__(self) -> None:
        self._engines: dict[str, Engine] = {}
        self._states: dict[str, EngineLifecycle] = {}
        self._start_order: list[str] = []

    def register(self, engine: Engine) -> None:
        if engine.engine_id in self._engines:
            raise EngineLifecycleError(f"Engine is already registered: {engine.engine_id}")
        self._engines[engine.engine_id] = engine
        self._states[engine.engine_id] = EngineLifecycle.REGISTERED

    def initialize_and_start(self, container: ServiceContainer) -> None:
        order = self._resolve_order()
        started: list[str] = []
        try:
            for engine_id in order:
                engine = self._engines[engine_id]
                engine.initialize(container)
                self._states[engine_id] = EngineLifecycle.INITIALIZED
                engine.start()
                self._states[engine_id] = EngineLifecycle.STARTED
                started.append(engine_id)
            self._start_order = started
        except Exception as exc:
            self._states[engine_id] = EngineLifecycle.FAILED
            self._shutdown_ids(reversed(started))
            raise EngineLifecycleError(f"Engine startup failed: {engine_id}") from exc

    def shutdown(self) -> None:
        self._shutdown_ids(reversed(self._start_order))
        self._start_order.clear()

    def state(self, engine_id: str) -> EngineLifecycle:
        try:
            return self._states[engine_id]
        except KeyError as exc:
            raise EngineLifecycleError(f"Engine is not registered: {engine_id}") from exc

    def states(self) -> tuple[tuple[str, EngineLifecycle], ...]:
        return tuple(sorted(self._states.items()))

    def _shutdown_ids(self, identifiers: Iterable[str]) -> None:
        for engine_id in identifiers:
            try:
                self._engines[engine_id].shutdown()
                self._states[engine_id] = EngineLifecycle.STOPPED
            except Exception:
                self._states[engine_id] = EngineLifecycle.FAILED

    def _resolve_order(self) -> tuple[str, ...]:
        visiting: set[str] = set()
        visited: set[str] = set()
        result: list[str] = []

        def visit(engine_id: str) -> None:
            if engine_id in visiting:
                raise EngineLifecycleError("Circular Engine dependency detected")
            if engine_id in visited:
                return
            engine = self._engines[engine_id]
            visiting.add(engine_id)
            for dependency in engine.dependencies:
                if dependency not in self._engines:
                    raise EngineLifecycleError(
                        f"Required Engine dependency is not registered: {dependency}"
                    )
                visit(dependency)
            visiting.remove(engine_id)
            visited.add(engine_id)
            result.append(engine_id)

        for identifier in self._engines:
            visit(identifier)
        return tuple(result)
