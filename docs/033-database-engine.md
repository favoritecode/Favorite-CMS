# Favorite CMS

Document ID: 033

Title: Database Engine

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

Next Document:

034-database-migration-engine.md

---

# 1. Purpose

This document defines the Favorite CMS Database Engine.

The Database Engine provides normalized relational database connectivity, SQLAlchemy integration, session lifecycle, and transaction infrastructure for approved Engines and Plugins.

The frozen stack uses SQLite for development and PostgreSQL for production.

---

# 2. Objectives

The Database Engine must provide:

* SQLAlchemy Integration
* Connection Lifecycle
* Session or Unit-of-Work Boundary
* Transaction Coordination
* SQLite Development Support
* PostgreSQL Production Support
* Provider-neutral Data Access
* Engine and Plugin Data Isolation
* Constraint and Integrity Boundary
* Safe Query Execution
* Health and Testing Integration

---

# 3. Database Provider

A Database Provider represents the active relational database implementation.

Favorite CMS supports SQLite for local development and PostgreSQL for production.

Business code must not depend on provider-specific behavior unless an approved contract explicitly requires it.

---

# 4. SQLAlchemy Boundary

SQLAlchemy is the approved ORM and database toolkit.

Engines and Plugins may use approved SQLAlchemy-based repositories, models, and services.

Direct ad-hoc connections outside the Database Engine must be avoided when a platform interface exists.

---

# 5. Connection Lifecycle

The Database Engine owns connection initialization, provider adapter setup, connection reuse or pooling where applicable, health verification, and controlled shutdown.

Exact pooling behavior may differ between SQLite and PostgreSQL.

---

# 6. Session Lifecycle

Database sessions or units of work must have explicit lifecycle boundaries.

A session must not leak across unrelated requests, Jobs, Plugins, or long-lived application scopes without an approved contract.

---

# 7. Transaction Boundary

Transactions are controlled by the component that owns the atomic business operation, using Database Engine transaction support.

The Database Engine provides transaction primitives but must not invent business transaction grouping across unrelated Engines.

---

# 8. Commit and Rollback

State-changing operations may commit only after required validation succeeds.

Failed transactional operations must roll back according to the owning operation's contract.

Rollback does not automatically mean retry.

---

# 9. Data Ownership

Database tables and persisted entities remain owned by the Engine or Plugin that defines their business meaning.

The Database Engine owns connectivity and transaction infrastructure, not Content, Media, Users, Settings, or Plugin business data.

---

# 10. Repository Boundary

Other components should call an owner's public service contract instead of directly querying its tables.

Cross-component direct table access or joins require an explicit integration contract.

---

# 11. Plugin Data Isolation

Plugins may persist Plugin-owned data through approved database interfaces.

A Plugin must not modify another Plugin's private tables, models, or migrations without an explicit dependency contract.

---

# 12. Schema Boundary

The Database Engine may expose metadata required by the Database Migration Engine.

Schema evolution belongs to Document 034.

Normal request handling must not silently rewrite schema.

---

# 13. Database Constraints

Database constraints may protect integrity.

They complement domain validation and must be tested for SQLite/PostgreSQL compatibility when behavior may differ.

---

# 14. Query Safety

Database access must use SQLAlchemy or parameterized query construction.

Client-controlled input must not be concatenated into executable SQL.

Dynamic identifiers or sorting rules must come from approved contracts.

---

# 15. Concurrency Boundary

Concurrent updates must preserve data integrity according to the owning Engine's contract.

The Database Engine must not promise one universal locking strategy.

Any optimistic or pessimistic concurrency model must be explicitly defined where required.

---

# 16. SQLite Development

SQLite is the approved development database.

Development code must not depend on SQLite-only behavior that silently fails against PostgreSQL production.

Portability-sensitive behavior should be covered by tests.

---

# 17. PostgreSQL Production

PostgreSQL is the approved production relational database.

Managed or self-hosted PostgreSQL may be used.

Provider-specific hosting, pooling, replication, and tuning remain deployment-specific.

---

# 18. Configuration and Secrets

Connection configuration is supplied through the Configuration Engine.

Database Credentials must not be embedded in source code, frontend bundles, or ordinary Logs.

---

# 19. Logging and Error Integration

Database failures must be normalized through the Error Handling Engine and logged safely through the Logging Engine.

Raw SQL containing sensitive values, connection strings, and provider Credentials must not be exposed publicly.

---

# 20. Health and Backup Boundaries

Observability may request lightweight approved database health checks.

Backup and Recovery may coordinate database backup/restore.

The Database Engine does not own backup retention, restore policy, or schema migration sequencing.

---

# 21. Testing Boundary

Tests may use isolated SQLite databases and approved PostgreSQL test environments.

Tests must never depend on the production database.

Provider portability and transaction behavior should be verified where relevant.

---

# 22. Failure Isolation

A failed database operation must not corrupt unrelated transactions.

Sessions and connections must be released safely after failure.

Database unavailability must produce controlled readiness and operation failures.

---

# 23. Compatibility and Non-Goals

Internal repositories may evolve while public Engine contracts remain stable.

Breaking schema changes must use the Database Migration Engine.

The Database Engine does not own business logic, schema migration sequencing, backup retention, Search ranking, Cache behavior, or API serialization.

---

# 24. Final Database Flow

A typical database operation follows:

1. The owning Engine or Plugin validates business input.
2. Obtain an approved session or unit of work.
3. Execute SQLAlchemy/parameterized operations.
4. Apply domain and database integrity rules.
5. Commit only when the owning operation succeeds.
6. Roll back and normalize failures when required.
7. Release the session or connection.

---

# 25. Codex Implementation Rules

Codex must:

* Use SQLAlchemy.
* Support SQLite development and PostgreSQL production.
* Centralize connection/session lifecycle.
* Keep domain ownership in Engines and Plugins.
* Never allow direct cross-component table access without an explicit contract.
* Use safe parameterized queries.
* Keep schema migration in Document 034.
* Keep Credentials out of source code and Logs.
* Never silently create or patch schema during ordinary request handling.

---

# 26. Final Acceptance Criteria

* [x] Database purpose, SQLAlchemy, providers, connections, sessions, transactions, ownership, repositories, Plugin isolation, schema, constraints, query safety, concurrency, SQLite/PostgreSQL defined.
* [x] Configuration, Error, Logging, Health, Backup, Testing, failure isolation, compatibility, final flow, and Codex rules defined.

---

# 27. Document Status

This document defines the Database Engine specification for Favorite CMS.

The Database Engine uses SQLAlchemy and supports SQLite in development and PostgreSQL in production while preserving domain ownership and provider portability.

Schema evolution belongs to the Database Migration Engine.

---

End of Document

Next Document:

034-database-migration-engine.md
