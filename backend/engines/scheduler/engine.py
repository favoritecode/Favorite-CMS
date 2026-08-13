"""UTC-aware schedule eligibility and Queue dispatch coordination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from threading import RLock
from types import MappingProxyType
from typing import Callable, Mapping

from backend.core.container import ServiceContainer
from backend.engines.errors import ErrorHandlingEngine, ErrorRecord
from backend.engines.logging import LogCategory, LogSource, LogSourceKind, LoggingEngine
from backend.engines.queue import QueueEngine, QueueError


class SchedulerError(ValueError):
    pass


class ScheduleState(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNAVAILABLE = "unavailable"


class MissedRunPolicy(StrEnum):
    SKIP = "skip"


@dataclass(frozen=True)
class OneTimeSchedule:
    run_at: datetime

    def __post_init__(self) -> None:
        _require_aware(self.run_at)


@dataclass(frozen=True)
class IntervalSchedule:
    first_run_at: datetime
    interval: timedelta

    def __post_init__(self) -> None:
        _require_aware(self.first_run_at)
        if self.interval <= timedelta(0):
            raise SchedulerError("Schedule interval must be positive")


ScheduleDefinition = OneTimeSchedule | IntervalSchedule


@dataclass
class ScheduledTask:
    task_id: str
    owner: str
    job_type: str
    producer: str
    payload: Mapping[str, object]
    schedule: ScheduleDefinition
    state: ScheduleState = ScheduleState.ACTIVE
    missed_run_policy: MissedRunPolicy = MissedRunPolicy.SKIP
    exclusive: bool = True
    next_trigger: datetime | None = None
    last_trigger: datetime | None = None
    last_failure: ErrorRecord | None = None
    owner_available: Callable[[], bool] = lambda: True

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.owner.strip():
            raise SchedulerError("Scheduled Task identity and owner are required")
        if not self.job_type.strip() or not self.producer.strip():
            raise SchedulerError("Scheduled Task Job contract is required")
        self.payload = MappingProxyType(dict(self.payload))
        if self.next_trigger is None:
            self.next_trigger = (
                self.schedule.run_at
                if isinstance(self.schedule, OneTimeSchedule)
                else self.schedule.first_run_at
            )


@dataclass(frozen=True)
class TriggerResult:
    task_id: str
    dispatched: bool
    job_id: str | None = None
    failure: ErrorRecord | None = None


class SchedulerEngine:
    engine_id = "scheduler"
    dependencies = ("queue",)

    def __init__(self) -> None:
        self._queue: QueueEngine | None = None
        self._errors: ErrorHandlingEngine | None = None
        self._logging: LoggingEngine | None = None
        self._tasks: dict[str, ScheduledTask] = {}
        self._running: set[str] = set()
        self._lock = RLock()
        self.ready = False

    def initialize(self, container: ServiceContainer) -> None:
        self._queue = container.resolve("engine.queue", QueueEngine)
        self._errors = container.resolve("core.errors", ErrorHandlingEngine)
        self._logging = container.resolve("core.logging", LoggingEngine)
        container.register("engine.scheduler", self)

    def start(self) -> None:
        self.ready = True

    def shutdown(self) -> None:
        with self._lock:
            self._running.clear()
        self.ready = False

    def register(self, task: ScheduledTask) -> None:
        if task.task_id in self._tasks:
            raise SchedulerError(f"Scheduled Task is already registered: {task.task_id}")
        self._tasks[task.task_id] = task

    def disable(self, task_id: str) -> None:
        self._task(task_id).state = ScheduleState.INACTIVE

    def enable(self, task_id: str) -> None:
        task = self._task(task_id)
        task.state = ScheduleState.ACTIVE if task.owner_available() else ScheduleState.UNAVAILABLE

    def remove(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    def cycle(self, now: datetime) -> tuple[TriggerResult, ...]:
        if not self.ready:
            raise SchedulerError("Scheduler Engine is unavailable")
        _require_aware(now)
        results: list[TriggerResult] = []
        for task in tuple(self._tasks.values()):
            if task.state is not ScheduleState.ACTIVE or task.next_trigger is None:
                continue
            if not task.owner_available():
                task.state = ScheduleState.UNAVAILABLE
                continue
            if task.next_trigger > now:
                continue
            with self._lock:
                if task.exclusive and task.task_id in self._running:
                    continue
                self._running.add(task.task_id)
            try:
                result = self._dispatch(task, now)
                results.append(result)
            finally:
                with self._lock:
                    self._running.discard(task.task_id)
        return tuple(results)

    def _dispatch(self, task: ScheduledTask, now: datetime) -> TriggerResult:
        try:
            submitted = self._require_queue().submit(
                task.job_type, task.producer, task.payload
            )
            task.last_trigger = now
            task.last_failure = None
            if isinstance(task.schedule, OneTimeSchedule):
                task.next_trigger = None
                task.state = ScheduleState.INACTIVE
            else:
                next_trigger = task.next_trigger
                assert next_trigger is not None
                while next_trigger <= now:
                    next_trigger += task.schedule.interval
                task.next_trigger = next_trigger
            return TriggerResult(task.task_id, True, submitted.job_id)
        except Exception as exc:
            failure = self._require_errors().normalize(
                exc, source=f"scheduler:{task.owner}", context={"operation_id": task.task_id}
            )
            task.last_failure = failure
            self._log_failure(failure)
            # No Scheduler retry or catch-up is invented. The due point remains unchanged.
            return TriggerResult(task.task_id, False, failure=failure)

    def _task(self, task_id: str) -> ScheduledTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise SchedulerError("Scheduled Task is not registered") from exc

    def _require_queue(self) -> QueueEngine:
        if self._queue is None:
            raise SchedulerError("Queue Engine is unavailable")
        return self._queue

    def _require_errors(self) -> ErrorHandlingEngine:
        if self._errors is None:
            raise SchedulerError("Scheduler Engine is not initialized")
        return self._errors

    def _log_failure(self, error: ErrorRecord) -> None:
        if self._logging is not None:
            self._logging.error(
                "Scheduled Task dispatch failed",
                source=LogSource(LogSourceKind.ENGINE, "scheduler"),
                category=LogCategory.ENGINE,
                context={"error_id": error.error_id, "operation_id": error.context.get("operation_id")},
            )


def _require_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SchedulerError("Schedule time must include an explicit time zone")

