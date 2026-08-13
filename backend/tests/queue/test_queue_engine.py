import pytest

from backend.core.container import ServiceContainer
from backend.engines.errors import ErrorHandlingEngine
from backend.engines.logging import LoggingEngine
from backend.engines.queue import (
    InMemoryQueueProvider,
    JobContract,
    JobStatus,
    QueueEngine,
    QueueError,
    RetryPolicy,
)


def started_queue(provider: object | None = None) -> QueueEngine:
    container = ServiceContainer()
    container.register("core.errors", ErrorHandlingEngine())
    container.register("core.logging", LoggingEngine())
    queue = QueueEngine(provider)  # type: ignore[arg-type]
    queue.initialize(container)
    queue.start()
    return queue


def test_enqueue_dequeue_execute_acknowledge_and_result() -> None:
    queue = started_queue(InMemoryQueueProvider())
    queue.register(JobContract("test.job.execute", "test.producer", lambda payload: None, lambda job: "done"))
    submitted = queue.submit("test.job.execute", "test.producer", {"resource_id": "r1"})
    assert submitted.status is JobStatus.PENDING
    completed = queue.process_next()
    assert completed is not None
    assert completed.status is JobStatus.COMPLETED
    assert completed.attempts == 1 and completed.result == "done"


def test_failed_job_has_controlled_state_without_implicit_retry() -> None:
    queue = started_queue()
    queue.register(
        JobContract(
            "test.job.fail", "test.producer", lambda payload: None,
            lambda job: (_ for _ in ()).throw(RuntimeError("private failure")),
        )
    )
    job_id = queue.submit("test.job.fail", "test.producer", {}).job_id
    result = queue.process_next()
    assert result is not None and result.status is JobStatus.FAILED
    assert result.attempts == 1
    assert "private failure" not in repr(result.failure.public())  # type: ignore[union-attr]
    assert queue.process_next() is None


def test_explicit_retry_policy_limits_attempts() -> None:
    queue = started_queue()
    queue.register(
        JobContract(
            "test.job.retry", "test.producer", lambda payload: None,
            lambda job: (_ for _ in ()).throw(RuntimeError("fail")),
            RetryPolicy(2, lambda error: True),
        )
    )
    job_id = queue.submit("test.job.retry", "test.producer", {}).job_id
    first = queue.process_next()
    assert first is not None and first.status is JobStatus.PENDING and first.attempts == 1
    second = queue.process_next()
    assert second is not None and second.status is JobStatus.FAILED and second.attempts == 2
    assert queue.result(job_id).attempts == 2


def test_delayed_job_and_cancellation() -> None:
    queue = started_queue()
    queue.register(JobContract("test.job.delayed", "test.producer", lambda payload: None, lambda job: None))
    job_id = queue.submit("test.job.delayed", "test.producer", {}, delay_seconds=60).job_id
    assert queue.process_next() is None
    assert queue.cancel(job_id)
    assert queue.result(job_id).status is JobStatus.CANCELLED


def test_duplicate_submissions_have_distinct_identity_without_exactly_once_claim() -> None:
    queue = started_queue()
    queue.register(JobContract("test.job.duplicate", "test.producer", lambda payload: None, lambda job: None))
    first = queue.submit("test.job.duplicate", "test.producer", {})
    second = queue.submit("test.job.duplicate", "test.producer", {})
    assert first.job_id != second.job_id


def test_worker_shutdown_is_deterministic() -> None:
    queue = started_queue()
    queue.shutdown()
    assert not queue.ready and not queue.worker_running
    with pytest.raises(QueueError, match="not running"):
        queue.dequeue()


def test_provider_failure_is_controlled() -> None:
    class BrokenProvider:
        def healthcheck(self) -> bool: return True
        def enqueue(self, job: object) -> None: raise RuntimeError("provider secret")
    queue = started_queue(BrokenProvider())
    queue.register(JobContract("test.job.provider", "test.producer", lambda payload: None, lambda job: None))
    with pytest.raises(QueueError, match="submission failed") as error:
        queue.submit("test.job.provider", "test.producer", {})
    assert "provider secret" not in str(error.value)

