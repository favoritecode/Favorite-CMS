"""Provider-neutral deferred execution with caller-driven workers.

The in-memory provider offers process-local, at-most-one active dequeue. It
does not claim persistence, exactly-once delivery, or distributed ordering.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from threading import RLock
from time import monotonic
import re
from types import MappingProxyType
from typing import Callable, Mapping, Protocol
from uuid import uuid4

from backend.core.container import ServiceContainer
from backend.engines.errors import ErrorHandlingEngine, ErrorRecord
from backend.engines.logging import LogCategory, LogSource, LogSourceKind, LoggingEngine


class QueueError(RuntimeError):
    pass


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


PayloadValidator = Callable[[Mapping[str, object]], None]
JobHandler = Callable[["Job"], object]
RetryPredicate = Callable[[ErrorRecord], bool]
_TYPE = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$")
_SENSITIVE = ("password", "credential", "token", "secret", "authorization", "cookie")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    should_retry: RetryPredicate

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise QueueError("Retry maximum attempts must be at least one")


@dataclass(frozen=True)
class JobContract:
    job_type: str
    producer: str
    validate_payload: PayloadValidator
    handler: JobHandler
    retry: RetryPolicy | None = None

    def __post_init__(self) -> None:
        if not _TYPE.fullmatch(self.job_type) or not self.producer.strip():
            raise QueueError("Job contract identity is invalid")


@dataclass
class Job:
    job_id: str
    job_type: str
    producer: str
    payload: Mapping[str, object]
    created_at: str
    available_at: float
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    result: object | None = None
    failure: ErrorRecord | None = None


@dataclass(frozen=True)
class JobResult:
    job_id: str
    status: JobStatus
    attempts: int
    result: object | None = None
    failure: ErrorRecord | None = None


class QueueProvider(Protocol):
    def enqueue(self, job: Job) -> None: ...
    def dequeue(self, now: float) -> Job | None: ...
    def acknowledge(self, job_id: str) -> None: ...
    def fail(self, job_id: str) -> None: ...
    def cancel(self, job_id: str) -> bool: ...
    def healthcheck(self) -> bool: ...


class InMemoryQueueProvider:
    def __init__(self) -> None:
        self._pending: deque[Job] = deque()
        self._running: dict[str, Job] = {}
        self._lock = RLock()

    def enqueue(self, job: Job) -> None:
        with self._lock:
            self._pending.append(job)

    def dequeue(self, now: float) -> Job | None:
        with self._lock:
            for _ in range(len(self._pending)):
                job = self._pending.popleft()
                if job.available_at <= now:
                    self._running[job.job_id] = job
                    return job
                self._pending.append(job)
            return None

    def acknowledge(self, job_id: str) -> None:
        with self._lock:
            if self._running.pop(job_id, None) is None:
                raise QueueError("Running Job is unavailable for acknowledgement")

    def fail(self, job_id: str) -> None:
        self.acknowledge(job_id)

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            for job in tuple(self._pending):
                if job.job_id == job_id:
                    self._pending.remove(job)
                    return True
            return False

    def healthcheck(self) -> bool:
        return True


class QueueEngine:
    engine_id = "queue"
    dependencies: tuple[str, ...] = ()

    def __init__(self, provider: QueueProvider | None = None) -> None:
        self._provider = provider
        self._contracts: dict[str, JobContract] = {}
        self._jobs: dict[str, Job] = {}
        self._errors: ErrorHandlingEngine | None = None
        self._logging: LoggingEngine | None = None
        self.ready = False
        self.worker_running = False

    def initialize(self, container: ServiceContainer) -> None:
        self._errors = container.resolve("core.errors", ErrorHandlingEngine)
        self._logging = container.resolve("core.logging", LoggingEngine)
        container.register("engine.queue", self)

    def start(self) -> None:
        if self._provider is None:
            self._provider = InMemoryQueueProvider()
        try:
            if not self._provider.healthcheck():
                raise QueueError("Queue Provider is unavailable")
        except QueueError:
            raise
        except Exception as exc:
            raise QueueError("Queue Provider is unavailable") from exc
        self.ready = True
        self.start_worker()

    def shutdown(self) -> None:
        self.stop_worker()
        self.ready = False

    def start_worker(self) -> None:
        if not self.ready:
            raise QueueError("Queue Engine is unavailable")
        self.worker_running = True

    def stop_worker(self) -> None:
        self.worker_running = False

    def healthcheck(self) -> bool:
        try: return self.ready and self.worker_running and self._require_provider().healthcheck()
        except Exception: return False

    def register(self, contract: JobContract) -> None:
        if contract.job_type in self._contracts:
            raise QueueError(f"Job contract is already registered: {contract.job_type}")
        self._contracts[contract.job_type] = contract

    def submit(
        self,
        job_type: str,
        producer: str,
        payload: Mapping[str, object],
        *,
        delay_seconds: float = 0,
    ) -> JobResult:
        if not self.ready:
            raise QueueError("Queue Engine is unavailable")
        if delay_seconds < 0:
            raise QueueError("Job delay must not be negative")
        contract = self._contract(job_type)
        if producer != contract.producer:
            raise QueueError("Job producer is not approved for this contract")
        safe_payload = _validate_payload(payload)
        contract.validate_payload(safe_payload)
        job = Job(
            job_id=str(uuid4()),
            job_type=job_type,
            producer=producer,
            payload=MappingProxyType(dict(safe_payload)),
            created_at=datetime.now(timezone.utc).isoformat(),
            available_at=monotonic() + delay_seconds,
        )
        try:
            self._require_provider().enqueue(job)
        except Exception as exc:
            raise QueueError("Job submission failed") from exc
        self._jobs[job.job_id] = job
        return self.result(job.job_id)

    def dequeue(self) -> Job | None:
        if not self.worker_running:
            raise QueueError("Queue Worker is not running")
        try:
            job = self._require_provider().dequeue(monotonic())
        except Exception as exc:
            raise QueueError("Job dequeue failed") from exc
        if job is not None:
            job.status = JobStatus.RUNNING
        return job

    def process_next(self) -> JobResult | None:
        job = self.dequeue()
        if job is None:
            return None
        contract = self._contract(job.job_type)
        job.attempts += 1
        try:
            contract.validate_payload(job.payload)
            job.result = contract.handler(job)
            job.failure = None
            job.status = JobStatus.COMPLETED
            self._require_provider().acknowledge(job.job_id)
        except Exception as exc:
            error = self._require_errors().normalize(
                exc, source=f"queue-handler:{job.job_type}", context={"job_id": job.job_id}
            )
            job.failure = error
            self._log_failure(error)
            try:
                self._require_provider().fail(job.job_id)
            except Exception:
                pass
            if contract.retry is not None and job.attempts < contract.retry.max_attempts \
                    and contract.retry.should_retry(error):
                job.status = JobStatus.PENDING
                self._require_provider().enqueue(job)
            else:
                job.status = JobStatus.FAILED
        return self.result(job.job_id)

    def cancel(self, job_id: str) -> bool:
        job = self._job(job_id)
        if job.status is not JobStatus.PENDING:
            return False
        try:
            cancelled = self._require_provider().cancel(job_id)
        except Exception as exc:
            raise QueueError("Job cancellation failed") from exc
        if cancelled:
            job.status = JobStatus.CANCELLED
        return cancelled

    def result(self, job_id: str) -> JobResult:
        job = self._job(job_id)
        return JobResult(job.job_id, job.status, job.attempts, job.result, job.failure)

    def _contract(self, job_type: str) -> JobContract:
        try:
            return self._contracts[job_type]
        except KeyError as exc:
            raise QueueError(f"Job contract is not registered: {job_type}") from exc

    def _job(self, job_id: str) -> Job:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise QueueError("Job is not registered") from exc

    def _require_provider(self) -> QueueProvider:
        if self._provider is None:
            raise QueueError("Queue Provider is unavailable")
        return self._provider

    def _require_errors(self) -> ErrorHandlingEngine:
        if self._errors is None:
            raise QueueError("Queue Engine is not initialized")
        return self._errors

    def _log_failure(self, error: ErrorRecord) -> None:
        if self._logging is not None:
            self._logging.error(
                "Queue Job failed",
                source=LogSource(LogSourceKind.ENGINE, "queue"),
                category=LogCategory.ENGINE,
                context={"error_id": error.error_id, "job_id": error.context.get("job_id")},
            )


def _validate_payload(payload: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise QueueError("Job Payload must be structured data")
    for key in payload:
        if not isinstance(key, str) or any(fragment in key.lower() for fragment in _SENSITIVE):
            raise QueueError("Job Payload contains a prohibited field")
    return payload
