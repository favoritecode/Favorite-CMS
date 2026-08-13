# Favorite CMS

Document ID: 040

Title: Testing Strategy

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
* 035-scheduler-engine.md
* 036-admin-architecture.md
* 037-security-architecture.md
* 038-backup-recovery.md
* 039-observability-health.md

Next Document:

041-installation-bootstrap.md

---

# 1. Purpose

This document defines the Favorite CMS Testing Strategy.

Testing must verify architecture contracts, Engine behavior, Plugin and Theme isolation, failure safety, provider portability, and end-to-end workflows before implementation is considered complete.

The frozen testing stack includes Pytest and Playwright.

---

# 2. Objectives

Testing must cover:

* Unit Tests
* Integration Tests
* API Tests
* Database and Migration Tests
* Storage/Cache/Event/Queue/Scheduler Tests
* Plugin and Theme Contract Tests
* Security Tests
* Update and Backup Tests
* Admin and Public End-to-End Tests
* Production-readiness Regression Tests

---

# 3. Test Layers

Unit tests validate isolated logic.

Integration tests validate boundaries between real components.

End-to-end tests validate critical User and operational workflows.

No single test layer replaces the others.

---

# 4. Pytest and Playwright

Pytest is the approved backend testing framework.

Playwright is the approved browser end-to-end framework for Admin and public workflows.

Tests must remain runnable locally by the solo developer.

---

# 5. Unit and Integration Tests

Unit tests should cover validation, normalization, resolution, fallback, dependency ordering, and state transitions.

Integration tests should cover API-to-Engine, Engine-to-Database, Media-to-Storage, Scheduler-to-Queue, Plugin registration, Theme rendering, Authentication-to-Permission, and Update-to-Migration.

---

# 6. API, Routing, and Rendering Tests

Tests must validate request validation, Authentication, Permission, response/error normalization, Routing integration, deterministic Route matching, and Rendering consumption of resolved Route Context.

Regression tests must prevent duplicate Routing ownership inside Rendering or API.

---

# 7. Database and Migration Tests

Database tests must cover SQLAlchemy sessions, transactions, rollback, constraints, query safety, and provider portability.

Migration tests must cover ordering, applied history, provider compatibility, failure behavior, and irreversible declarations when applicable.

SQLite and PostgreSQL differences must be tested where relevant.

---

# 8. Storage, Cache, Event, Queue, and Scheduler Tests

Storage adapters should pass a common contract suite.

Cache tests must verify scope and invalidation safety.

Event tests must verify listener isolation.

Queue tests must verify Job lifecycle and retry boundaries.

Scheduler tests must verify trigger calculations, duplicate protection, and Queue dispatch.

---

# 9. Authentication and Permission Tests

Tests must cover authenticated/anonymous contexts, invalid or expired Authentication state, ownership checks, Permission denial, and the rule that Authentication success does not imply authorization.

---

# 10. Plugin and Theme Tests

Plugin tests should cover manifests, dependencies, lifecycle, API/Admin registration, database ownership, Storage scope, Permissions, updates, and failure isolation.

Theme tests should cover manifests, dependencies, rendering, localization, Plugin presentation overrides, settings persistence, and fallback.

---

# 11. Security Tests

Security tests must cover input validation, SQL injection resistance, output escaping/sanitization contracts, upload/path safety, Plugin/Theme isolation, secret redaction, Authentication/Permission boundaries, arbitrary-handler prevention, and Update package validation.

---

# 12. Error, Logging, Update, and Backup Tests

Tests should verify Error normalization, public/internal separation, sensitive Log redaction, Update preflight/rollback, Backup creation, verification, and isolated Restore validation.

---

# 13. Admin and Public E2E Tests

Playwright must cover Admin login, Permission denial, Content/Media flows, Settings, Plugin/Theme management, diagnostics, public Routing/Rendering, Search, Localization, missing Resources, and graceful Plugin/Theme failure.

---

# 14. Test Data and Determinism

Tests must use synthetic or approved non-production data.

They must not depend on production secrets, production databases, or destructive external services.

Time, randomness, Queue execution, and provider behavior should be controlled where needed.

---

# 15. CI Boundary

GitHub-based CI may run linting, backend tests, frontend tests, migrations, builds, and selected E2E tests.

Exact CI provider configuration is implementation detail, but local execution must remain supported.

---

# 16. Coverage and Regression Gates

This architecture does not impose an arbitrary global coverage percentage.

Critical security, migration, update, Authentication, Permission, data-integrity, and failure-isolation paths require explicit tests.

Architecture conflicts fixed in Documents 011, 013, and 026 require regression protection.

---

# 17. Release Test Gate

A production release must not proceed when required automated tests, migration validation, build validation, or critical E2E checks fail unless an explicit operational exception is documented.

---

# 18. Non-Goals

Testing does not require one mocking library, one cloud CI vendor, a fixed coverage percentage, production data in tests, or every test to be end-to-end.

---

# 19. Codex Testing Rules

Codex must:

* Create tests with each implemented module.
* Use Pytest for backend and Playwright for browser E2E.
* Keep tests isolated from production.
* Test failure paths as well as success paths.
* Add regression tests for architecture ownership conflicts.
* Test SQLite/PostgreSQL differences when relevant.
* Never mark a module complete while required tests fail.
* Never invent external providers merely to satisfy tests.

---

# 20. Final Acceptance Criteria

* [x] Unit, integration, API, Routing, Rendering, Database, Migration, Storage, Cache, Event, Queue, Scheduler, Authentication, Permission, Plugin, Theme, Security, Error, Logging, Update, Backup, Admin, and public testing defined.
* [x] Test data, determinism, CI, coverage, regression, release gates, and Codex rules defined.

---

# 21. Document Status

This document defines the Testing Strategy for Favorite CMS.

Pytest and Playwright are the approved testing frameworks.

Testing is part of implementation completion, not a later optional phase.

---

End of Document

Next Document:

041-installation-bootstrap.md
