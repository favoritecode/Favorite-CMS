# Favorite CMS

Document ID: 035

Title: Scheduler Engine

Version: 1.0.0

Status: Draft

Author: Favorite CMS

Created: 2026-08-11

Last Updated: 2026-08-11

Depends On:

* 001-project-overview.md
* 002-system-architecture.md
* 003-project-principles.md
* 004-technology-stack.md
* 005-folder-structure.md
* 006-development-workflow.md
* 007-core-engine.md
* 008-extension-system.md
* 009-theme-engine.md
* 010-plugin-engine.md
* 011-rendering-engine.md
* 012-content-engine.md
* 013-media-engine.md
* 014-search-engine.md
* 015-user-engine.md
* 016-permission-engine.md
* 017-cache-engine.md
* 018-event-engine.md
* 019-queue-engine.md
* 020-notification-engine.md
* 021-settings-engine.md
* 022-menu-engine.md
* 023-seo-engine.md
* 024-update-engine.md
* 025-authentication-engine.md
* 026-api-engine.md
* 027-storage-engine.md
* 028-localization-engine.md
* 029-routing-engine.md
* 030-logging-engine.md
* 031-error-handling-engine.md
* 032-configuration-engine.md
* 033-database-engine.md
* 034-database-migration-engine.md

Next Document:

036-admin-architecture.md

---

# 1. Purpose

This document defines the Favorite CMS Scheduler Engine.

The Scheduler Engine coordinates when approved recurring or future tasks become eligible to trigger.

It must remain separate from Queue execution and business logic.

---

# 2. Objectives

The Scheduler Engine must provide:

* Scheduled Task Registration
* Schedule Definitions
* Recurring and One-time Trigger Boundaries
* Time-aware Resolution
* Task Activation State
* Plugin Schedule Integration
* Queue Integration
* Concurrency and Locking Boundary
* Missed Schedule Handling
* Cancellation and Disablement
* Failure Isolation
* Observability

No specific cron library or scheduler provider is required.

---

# 3. Scheduled Task

A Scheduled Task is an approved reference to work that may be triggered at a future time or recurrence.

It must identify an owner, stable identifier, handler or Job contract, schedule, activation state, and compatibility metadata.

---

# 4. Schedule Definition

A Schedule Definition describes when a task is eligible to trigger.

The exact expression format must be defined by the implementation contract.

Codex must not invent undocumented schedule syntax.

---

# 5. Task Owner

Every Scheduled Task must have one owner such as a platform Engine or Plugin.

The owner defines business purpose and handler behavior.

The Scheduler Engine only decides when the task becomes eligible.

---

# 6. Trigger Boundary

Preferred architecture:

Scheduler Engine
→ approved handler or Job request
→ Queue Engine when deferred execution is appropriate
→ owning Engine or Plugin

Direct execution is allowed only when an explicit contract supports it.

---

# 7. Queue Integration

The Queue Engine owns asynchronous Job execution, retries, workers, and Job status.

The Scheduler Engine may submit approved Jobs at the scheduled time but must not duplicate Queue retry behavior.

---

# 8. Time and Time Zone

Schedule evaluation must use an explicit time basis.

User, site, or deployment time zones must not be guessed.

Time-zone-aware schedules must declare their context.

---

# 9. Recurring and One-time Schedules

Recurring schedules must produce deterministic future trigger points.

One-time schedules must not repeatedly trigger after successful dispatch.

Process restarts must not silently create duplicate dispatch when the implementation supports deduplication.

---

# 10. Registration and Plugin Lifecycle

Engines and Plugins register schedules through approved interfaces.

Registration validates identity, owner, schedule, handler availability, and dependencies.

Disabled or invalid Plugins must not continue receiving scheduled dispatches.

---

# 11. Activation State

Schedules may be active, inactive, or unavailable according to an explicit lifecycle contract.

Changing activation state must not silently delete schedule history.

---

# 12. Concurrency and Idempotency

The Scheduler must protect exclusive tasks from duplicate concurrent trigger when the contract requires it.

The owning Job or operation remains responsible for business idempotency where needed.

---

# 13. Missed Schedules

If a trigger time passes while the scheduler is unavailable, missed-run behavior must be explicit.

Possible behavior may be skip, trigger once on recovery, or another defined policy.

Codex must not invent catch-up behavior.

---

# 14. Retry Boundary

Scheduler dispatch failure and Job execution failure are separate conditions.

Queue retry belongs to the Queue Engine.

Scheduler retry must be explicitly defined and must not create duplicate Jobs.

---

# 15. Cancellation and Removal

Disabling or removing a schedule must follow owner lifecycle.

Removing a schedule must not automatically cancel an already-dispatched Queue Job unless an explicit contract exists.

---

# 16. Settings and Configuration

Scheduler infrastructure configuration belongs to the Configuration Engine.

Application-managed schedule settings may be stored through Settings or the owning component when explicitly supported.

---

# 17. Authentication and Permission

Administrative create, edit, disable, or manual-trigger operations may require Authentication and Permission checks.

Schedule ownership is not authorization.

---

# 18. Logging, Error, Event, and Observability

Trigger evaluation and dispatch failures may be logged and normalized safely.

The Scheduler may publish approved lifecycle Events only when exact Event Names and payload contracts are defined.

Diagnostics may expose next trigger, last trigger, owner, activation state, and safe failure references.

---

# 19. Failure Isolation and Security

One broken Scheduled Task must not stop unrelated schedules.

Handler references must come from trusted registration.

Client-controlled values must never select arbitrary executable callables or code.

---

# 20. Compatibility and Non-Goals

Stable Scheduled Task identifiers should remain compatible across non-breaking updates.

The Scheduler Engine does not own Queue workers, business logic, Queue retry policy, User calendar functionality, external calendar synchronization, or Notification delivery.

---

# 21. Final Scheduler Flow

A scheduler cycle follows:

1. Load active registered schedules.
2. Resolve current time using the approved time basis.
3. Determine tasks eligible to trigger.
4. Apply concurrency and duplicate-dispatch protections.
5. Build approved trigger context.
6. Dispatch the owning handler or Queue Job.
7. Record the trigger result.
8. Calculate the next trigger when recurring.

---

# 22. Codex Implementation Rules

Codex must:

* Keep Scheduler and Queue responsibilities separate.
* Keep schedule ownership explicit.
* Use deterministic time and time-zone handling.
* Disable Plugin schedules when their Plugin is unavailable.
* Never invent missed-run, retry, or catch-up policies.
* Never execute arbitrary client-selected callables.
* Keep secrets behind Configuration.
* Keep one failed task isolated from unrelated schedules.

---

# 23. Final Acceptance Criteria

* [x] Scheduler purpose, tasks, schedule definitions, ownership, Queue boundary, time handling, recurring/one-time behavior, registration, Plugin lifecycle, activation, concurrency, idempotency, missed runs, retry, cancellation defined.
* [x] Configuration, Authentication, Permission, Logging, Error, Events, Observability, failure isolation, Security, compatibility, final flow, and Codex rules defined.

---

# 24. Document Status

This document defines the Scheduler Engine specification for Favorite CMS.

The Scheduler Engine decides when approved work is triggered. Queue execution and business behavior remain owned by their applicable systems.

No specific cron engine, scheduler library, distributed-lock provider, or external scheduling service is required.

---

End of Document

Next Document:

036-admin-architecture.md
