from datetime import datetime, timezone

from backend.bootstrap import build_kernel
from backend.engines.events import EventEngine
from backend.engines.notifications import NotificationEngine
from backend.engines.queue import JobContract, JobStatus, QueueEngine
from backend.engines.scheduler import OneTimeSchedule, ScheduledTask, SchedulerEngine


def test_core_bootstraps_and_deterministically_shuts_down_phase3() -> None:
    kernel = build_kernel()
    kernel.bootstrap()
    events = kernel.container.resolve("engine.events", EventEngine)
    queue = kernel.container.resolve("engine.queue", QueueEngine)
    notifications = kernel.container.resolve("engine.notifications", NotificationEngine)
    scheduler = kernel.container.resolve("engine.scheduler", SchedulerEngine)
    assert events.ready
    assert queue.ready and queue.worker_running
    assert notifications.ready
    assert scheduler.ready
    kernel.shutdown()
    assert not events.ready
    assert not queue.ready and not queue.worker_running
    assert not notifications.ready
    assert not scheduler.ready


def test_scheduler_submits_to_queue_without_executing_job_itself() -> None:
    kernel = build_kernel()
    kernel.bootstrap()
    queue = kernel.container.resolve("engine.queue", QueueEngine)
    scheduler = kernel.container.resolve("engine.scheduler", SchedulerEngine)
    executed: list[str] = []
    queue.register(
        JobContract(
            "test.integration.deferred",
            "test.integration",
            lambda payload: None,
            lambda job: executed.append(job.job_id),
        )
    )
    due = datetime(2030, 1, 1, tzinfo=timezone.utc)
    scheduler.register(
        ScheduledTask(
            "integration-task", "test.integration", "test.integration.deferred",
            "test.integration", {}, OneTimeSchedule(due),
        )
    )
    trigger = scheduler.cycle(due)[0]
    assert trigger.dispatched and trigger.job_id is not None
    assert executed == []
    assert queue.result(trigger.job_id).status is JobStatus.PENDING
    queue.process_next()
    assert executed == [trigger.job_id]

