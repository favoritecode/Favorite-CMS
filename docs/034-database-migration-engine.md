# Favorite CMS

Document ID: 034

Title: Database Migration Engine

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

Next Document:

035-scheduler-engine.md

---

# 1. Purpose

This document defines the Favorite CMS Database Migration Engine.

It coordinates versioned relational schema changes for platform Engines and Plugins.

Schema evolution must be explicit, ordered, reviewable, provider-compatible, and failure-safe.

---

# 2. Objectives

The Database Migration Engine must provide:

* Migration Identification
* Schema Version Tracking
* Ordered Upgrade Execution
* Downgrade Boundary
* Platform and Plugin Migration Registration
* Dependency-aware Ordering
* Preflight Validation
* Migration Locking
* Transactional Migration Support
* Failure Recovery
* Update and Backup Integration
* SQLite and PostgreSQL Compatibility

---

# 3. Migration

A Migration is a versioned unit of schema or required compatibility change.

It must have a stable identifier, owner, ordering information, upgrade behavior, compatibility metadata, and other explicitly required fields.

---

# 4. Migration Owner

Every Migration must have one owner such as a platform Engine or Plugin.

The owner remains responsible for the schema objects and data meaning changed by the Migration.

---

# 5. Schema Version History

Applied migration state must be recorded explicitly.

The platform must not infer migration state only from table existence.

Migration history is long-lived compatibility data.

---

# 6. Registration and Ordering

Platform and Plugin migrations register through approved interfaces.

Execution order must be deterministic and dependency-safe.

Circular or unresolved dependencies must block the affected migration set.

---

# 7. Preflight Validation

Before migration, validate database connectivity, current migration state, dependencies, provider compatibility, ownership, and Update prerequisites when applicable.

---

# 8. Migration Lock

Only one incompatible migration sequence should execute against the same database at a time.

The exact locking mechanism remains provider-specific.

Failure to acquire the required lock must stop that migration attempt safely.

---

# 9. Transaction Boundary

Migrations should use transactions where the provider and operation support them safely.

The system must not assume every schema operation is fully transactional on every supported provider.

---

# 10. Upgrade and Downgrade

Upgrade moves the schema from an approved earlier state to a later supported state.

Downgrade is optional unless explicitly defined.

Irreversible migrations must declare that limitation clearly.

---

# 11. Data Transformation Boundary

A schema Migration may perform controlled data transformations required for compatibility.

Large business workflows, imports, indexing, and unrelated background processing must not be hidden inside schema migrations.

---

# 12. Plugin Migrations

Plugin migrations must remain scoped to Plugin-owned schema unless an explicit dependency contract permits shared changes.

A Plugin update must not modify another Plugin's private tables.

---

# 13. Update Integration

Preferred flow:

Update preflight
→ Migration preflight
→ Migration execution
→ Migration validation
→ Update activation or continuation

The Update Engine owns package activation and overall rollback policy.

---

# 14. Backup Boundary

A migration may require a verified recovery point before high-risk or irreversible changes.

Backup creation, verification, retention, and restore belong to Backup and Recovery.

---

# 15. SQLite and PostgreSQL Compatibility

Migrations expected to support development must be tested against SQLite.

Production migrations must support PostgreSQL.

Provider differences must not create inconsistent migration history.

---

# 16. Drift Detection Boundary

The system may detect schema state that does not match recorded migration history.

Detected drift must produce a controlled diagnostic and must not be silently rewritten.

---

# 17. Failure and Recovery

A failed Migration must never be recorded as successfully applied.

Recovery may include transaction rollback, backup restore, or a corrective Migration.

The Migration Engine must not invent unsafe automatic rollback for irreversible changes.

---

# 18. Logging, Error, and Observability

Migration lifecycle and failures may be logged using safe metadata.

Failures must be normalized through the Error Handling Engine.

Admin/Observability may expose version, pending state, and safe failure references without exposing secrets or sensitive SQL.

---

# 19. Security

Only authorized operational paths may execute migrations.

Public requests, Themes, or ordinary Plugin input must not trigger arbitrary migration code.

---

# 20. Compatibility and Non-Goals

Applied Migration definitions should not be casually rewritten.

New corrective behavior should normally use a new Migration.

The Migration Engine does not own ordinary queries, backup retention, Update package validation outside migration prerequisites, or Plugin uninstall data deletion unless explicitly defined.

---

# 21. Final Migration Flow

A migration sequence follows:

1. Discover registered migrations.
2. Read migration history.
3. Resolve dependency order.
4. Validate provider compatibility and prerequisites.
5. Acquire the migration lock.
6. Verify any required recovery point.
7. Execute each Migration with the strongest safe transaction boundary.
8. Validate the result.
9. Record only successful Migration identifiers.
10. Release the lock and report the result.

---

# 22. Codex Implementation Rules

Codex must:

* Keep migration history explicit.
* Keep Migration ownership explicit.
* Use deterministic dependency ordering.
* Support SQLite and PostgreSQL.
* Never mark failed migrations as applied.
* Never assume every Migration is reversible.
* Never silently modify already-applied Migration definitions.
* Keep Plugin migrations isolated.
* Never execute arbitrary migration code from public request input.

---

# 23. Final Acceptance Criteria

* [x] Migration, ownership, history, registration, ordering, preflight, locking, transaction, upgrade/downgrade, data transformation, Plugin, Update, Backup, provider compatibility, drift, failure/recovery, Logging/Observability/Security defined.
* [x] Final flow and Codex rules defined.

---

# 24. Document Status

This document defines the Database Migration Engine specification for Favorite CMS.

Schema evolution must remain explicit and versioned, separate from ordinary Database Engine behavior and from Update package ownership.

No specific migration framework is mandated beyond compatibility with the approved Python/SQLAlchemy stack.

---

End of Document

Next Document:

035-scheduler-engine.md
