from datetime import datetime, timedelta, timezone

import pytest

from backend.core.container import ServiceContainer
from backend.engines.errors import ErrorHandlingEngine
from backend.engines.logging import LoggingEngine
from backend.engines.queue import JobContract, QueueEngine
from backend.engines.scheduler import (
    IntervalSchedule,
    OneTimeSchedule,
    ScheduleState,
    ScheduledTask,
    SchedulerEngine,
    SchedulerError,
)


def started_pair() -> tuple[SchedulerEngine, QueueEngine]:
    container = ServiceContainer()
    container.register("core.errors", ErrorHandlingEngine())
    container.register("core.logging", LoggingEngine())
    queue = QueueEngine()
    queue.initialize(container)
    queue.start()
    scheduler = SchedulerEngine()
    scheduler.initialize(container)
    scheduler.start()
    return scheduler, queue


def test_one_time_schedule_dispatches_once_to_queue() -> None:
    scheduler, queue = started_pair()
    queue.register(JobContract("test.schedule.once", "test.owner", lambda payload: None, lambda job: None))
    due = datetime(2030, 1, 1, tzinfo=timezone.utc)
    task = ScheduledTask(
        "once", "test.owner", "test.schedule.once", "test.owner", {}, OneTimeSchedule(due)
    )
    scheduler.register(task)
    result = scheduler.cycle(due)
    assert len(result) == 1 and result[0].dispatched
    assert task.state is ScheduleState.INACTIVE and task.next_trigger is None
    assert scheduler.cycle(due + timedelta(days=1)) == ()


def test_recurring_schedule_uses_deterministic_next_trigger_and_skips_missed_runs() -> None:
    scheduler, queue = started_pair()
    queue.register(JobContract("test.schedule.repeat", "test.owner", lambda payload: None, lambda job: None))
    first = datetime(2030, 1, 1, tzinfo=timezone.utc)
    task = ScheduledTask(
        "repeat", "test.owner", "test.schedule.repeat", "test.owner", {},
        IntervalSchedule(first, timedelta(hours=1)),
    )
    scheduler.register(task)
    now = first + timedelta(hours=3, minutes=30)
    assert scheduler.cycle(now)[0].dispatched
    assert task.next_trigger == first + timedelta(hours=4)


def test_failed_schedule_is_isolated_and_not_retried_by_scheduler() -> None:
    scheduler, queue = started_pair()
    due = datetime(2030, 1, 1, tzinfo=timezone.utc)
    broken = ScheduledTask("broken", "test", "test.missing.job", "test", {}, OneTimeSchedule(due))
    queue.register(JobContract("test.healthy.job", "test", lambda payload: None, lambda job: None))
    healthy = ScheduledTask("healthy", "test", "test.healthy.job", "test", {}, OneTimeSchedule(due))
    scheduler.register(broken)
    scheduler.register(healthy)
    results = scheduler.cycle(due)
    assert [result.dispatched for result in results] == [False, True]
    assert broken.next_trigger == due
    assert broken.last_failure is not None


def test_unavailable_owner_disables_dispatch() -> None:
    scheduler, queue = started_pair()
    queue.register(JobContract("test.owner.job", "test", lambda payload: None, lambda job: None))
    due = datetime(2030, 1, 1, tzinfo=timezone.utc)
    task = ScheduledTask(
        "owner", "plugin-test", "test.owner.job", "test", {}, OneTimeSchedule(due),
        owner_available=lambda: False,
    )
    scheduler.register(task)
    assert scheduler.cycle(due) == ()
    assert task.state is ScheduleState.UNAVAILABLE


def test_naive_time_is_rejected_and_shutdown_is_deterministic() -> None:
    with pytest.raises(SchedulerError, match="time zone"):
        OneTimeSchedule(datetime(2030, 1, 1))
    scheduler, _ = started_pair()
    scheduler.shutdown()
    assert not scheduler.ready
    with pytest.raises(SchedulerError, match="unavailable"):
        scheduler.cycle(datetime.now(timezone.utc))


def test_disable_and_remove_do_not_cancel_dispatched_job() -> None:
    scheduler, queue = started_pair()
    queue.register(JobContract("test.cancel.boundary", "test", lambda payload: None, lambda job: None))
    due = datetime(2030, 1, 1, tzinfo=timezone.utc)
    task = ScheduledTask("cancel", "test", "test.cancel.boundary", "test", {}, OneTimeSchedule(due))
    scheduler.register(task)
    job_id = scheduler.cycle(due)[0].job_id
    scheduler.remove(task.task_id)
    assert job_id is not None
    assert queue.result(job_id).status.value == "pending"

