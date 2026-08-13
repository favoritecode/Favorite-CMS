# Favorite CMS

Document ID: 045

Title: Implementation Roadmap

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
* 040-testing-strategy.md
* 041-installation-bootstrap.md
* 042-deployment-architecture.md
* 043-production-operations.md
* 044-system-integration-contracts.md

Next Document:

None — Base Platform Documentation Complete

---

# 1. Purpose

This document defines the implementation roadmap for the Favorite CMS base platform.

Documents 001–044 are architecture and contract specifications.

This roadmap tells Codex and the solo developer how to implement, validate, integrate, and freeze the system without trying to build the entire CMS in one uncontrolled step.

---

# 2. Implementation Principles

Implementation must follow:

* Documentation is the source of truth.
* Implement one bounded document/module at a time.
* Do not invent undefined business requirements.
* Use public contracts between components.
* Add tests with each implementation step.
* Keep the platform runnable at milestone boundaries.
* Preserve provider-neutral abstractions.
* Prefer simple infrastructure suitable for a solo developer.
* Do not start optional business Plugins before the base platform is stable.

---

# 3. Completion Definition

A document is not implemented merely because classes exist.

Completion requires public contracts, tests, failure handling, security boundaries, integration behavior, and applicable acceptance criteria to pass.

---

# 4. Phase 0 — Repository Baseline

Implement Documents 001–006.

Gate: monorepo structure, backend/frontend startup skeleton, Git workflow, environment templates, and test commands exist without business features.

---

# 5. Phase 1 — Core Runtime

Implement:

* 007 Core Engine
* 008 Extension System foundation
* 032 Configuration Engine
* 031 Error Handling Engine
* 030 Logging Engine

Gate: Core boots, Configuration validates, Errors normalize, Logs work, and extension contracts exist without Database-dependent business features.

---

# 6. Phase 2 — Persistence Foundation

Implement:

* 033 Database Engine
* 034 Database Migration Engine
* 027 Storage Engine
* 017 Cache Engine

Gate: SQLAlchemy works with SQLite development and PostgreSQL production configuration; Migrations are versioned; Storage adapters pass contract tests; Cache failure is safely bypassed where supported.

---

# 7. Phase 3 — Messaging and Background Infrastructure

Implement:

* 018 Event Engine
* 019 Queue Engine
* 035 Scheduler Engine
* 020 Notification Engine

Gate: Events, Jobs, schedules, and Notifications use public contracts, failure isolation, and provider-neutral adapters.

---

# 8. Phase 4 — Identity and Security

Implement:

* 015 User Engine
* 025 Authentication Engine
* 016 Permission Engine
* 037 Security Architecture requirements

Gate: Authentication, authorization, protected APIs, secret boundaries, Plugin/Theme isolation, and security tests pass. Authentication success must never bypass Permission.

---

# 9. Phase 5 — Platform Data Engines

Implement:

* 021 Settings Engine
* 012 Content Engine
* 013 Media Engine
* 014 Search Engine
* 028 Localization Engine
* 022 Menu Engine
* 023 SEO Engine

Gate: Content and Media work through approved Database/Storage contracts; Settings/Configuration remain separate; Search, Localization, Menu, and SEO expose stable contracts.

---

# 10. Phase 6 — Extension Runtime

Complete and integrate:

* 008 Extension System
* 010 Plugin Engine
* 009 Theme Engine

Gate: Plugins and Themes can be discovered, validated, activated, disabled, and updated without Core modification; invalid extensions fail safely; Theme settings survive package updates.

---

# 11. Phase 7 — Routing, API, and Rendering

Implement:

* 029 Routing Engine
* 026 API Engine
* 011 Rendering Engine

Required ownership:

Routing Engine → Route registry and Route Context

API Engine → HTTP/API coordination

Rendering Engine → presentation composition

Gate: regression tests prove there is no duplicate Route resolver in Rendering and no competing Route registry in API.

---

# 12. Phase 8 — Admin Application

Implement 036 Admin Architecture and Admin integrations for completed Engines.

Gate: Admin operates through APIs, server-side Permissions are enforced, Plugin Admin failures are isolated, and critical Playwright flows pass.

---

# 13. Phase 9 — Update and Recovery

Implement:

* 024 Update Engine
* 038 Backup and Recovery

Gate: update preflight, compatibility, Migrations, activation, rollback where supported, Backup verification, and Restore validation work safely.

---

# 14. Phase 10 — Operational Readiness

Implement:

* 039 Observability and Health
* 041 Installation and Bootstrap
* 042 Deployment Architecture
* 043 Production Operations

Gate: clean installation, production Configuration, readiness checks, deployment sequence, Backup/Restore workflow, and operational diagnostics are validated.

---

# 15. Phase 11 — Full Testing Gate

Apply Document 040 across the complete platform.

Required categories include backend Pytest, Database/Migration portability, Plugin/Theme contracts, Security regressions, API/Routing/Rendering integration, Update/Backup tests, and Playwright Admin/public E2E.

Gate: no known critical architecture, security, migration, or data-integrity regression remains.

---

# 16. Phase 12 — Integration Freeze

Apply Document 044 as the final architecture checklist.

Every forbidden dependency must be absent.

Every cross-Engine call must use an approved public contract.

Provider-specific code must remain behind its owning adapter.

---

# 17. Milestones

Milestone A — Bootable Platform: Core, Configuration, Error, Logging, Database, Migration, basic Health.

Milestone B — Data-capable Platform: Settings, Content, Media, Storage, Cache, Search, User, Authentication, Permission.

Milestone C — Extensible Platform: Plugins and Themes safely discovered, validated, activated, disabled, and updated.

Milestone D — Complete Management Platform: Routing, API, Rendering, Admin, Menu, SEO, Localization, Queue, Scheduler, Notification, Update, Logs, Errors, Health integrated.

Milestone E — Production-ready Base CMS: installation, deployment, Backup/Restore, production operations, security, migration, and critical E2E gates pass.

---

# 18. Module Implementation Loop

For each module:

1. Read the document and dependencies.
2. Identify public interfaces and ownership.
3. Create the smallest required implementation skeleton.
4. Implement core behavior.
5. Implement failure handling and security.
6. Write unit tests.
7. Write integration tests with completed dependencies.
8. Run the relevant test suite.
9. Update implementation notes only when architecture is unchanged.
10. Mark complete only after acceptance criteria pass.

---

# 19. Codex Task Size

Do not prompt Codex to “build the CMS”.

Tasks should name one document or one bounded slice, such as Database session foundation, Storage adapter contract tests, or Routing conflict detection.

This keeps review scope manageable for a solo developer.

---

# 20. Architecture and Database Change Rules

If implementation reveals an architecture gap, update the relevant documentation before introducing a new dependency or ownership rule.

After migration infrastructure exists, all schema changes must use Document 034.

Application startup must never silently patch schema.

---

# 21. Plugin and Theme Start Gates

Business Plugins such as Movie, Streaming, Ecommerce, Subscription, Education, and other vertical features should begin only after the base dependencies they require are frozen, preferably after Milestone E.

Production-quality Themes should begin after Routing, Rendering, Theme Engine, Plugin presentation, Localization, Menu, SEO, and Settings are stable.

---

# 22. Performance Gate

Do not introduce distributed infrastructure solely for hypothetical scale.

First implement correctness with simple provider-neutral boundaries.

Optimize from measured bottlenecks while preserving public contracts.

---

# 23. Production Deployment Gate

Before first real production launch, confirm:

* PostgreSQL production Configuration validated.
* Production Storage Provider validated.
* Secrets protected.
* Required Migrations applied.
* Initial Admin secured.
* Backups created and verified.
* Restore procedure tested.
* Health/readiness working.
* Critical Admin/public Playwright tests passing.
* Security regression tests passing.
* Plugin/Theme dependencies valid.
* Logging and Error Handling safe.

---

# 24. Documentation Freeze Rule

Documents 001–045 form the base CMS architecture set.

After implementation begins, changes to frozen contracts must be deliberate, reviewed, and version-aware.

Business Plugin specifications should live outside this base sequence unless they truly change platform architecture.

---

# 25. Final Base Platform Scope

The base platform includes Core, extensions, Theme/Plugin Engines, Routing, API, Rendering, Content, Media, Search, User, Authentication, Permission, Cache, Events, Queue, Scheduler, Notification, Settings, Menu, SEO, Localization, Update, Storage, Logging, Error Handling, Configuration, Database, Migrations, Admin, Security, Backup, Observability, Testing, Installation, Deployment, and Production Operations.

Movie, Ecommerce, Subscription, Streaming, Education, and similar vertical features remain optional Plugin work.

---

# 26. Final Implementation Rules

Codex must never:

* Modify Core for an optional business feature.
* Let Themes own business logic.
* Let Plugins bypass public Engine contracts.
* Let Rendering resolve Routes.
* Let API maintain a competing Route registry.
* Let Media own a competing Storage Provider layer.
* Let Authentication imply Permission.
* Let Admin access Database or Storage Providers directly.
* Expose secrets in Logs, Errors, APIs, or frontend bundles.
* Invent undocumented schemas, providers, Event Names, role matrices, retry algorithms, ranking algorithms, or deployment vendors.
* Mark work complete while required tests fail.

---

# 27. Roadmap Completion Criteria

The base platform implementation is complete when:

* Documents 001–044 contracts are implemented or explicitly marked not applicable with architectural justification.
* Critical automated tests pass.
* Database Migrations are versioned and reproducible.
* Clean installation succeeds.
* Production deployment works against PostgreSQL and approved Storage.
* Backup creation and Restore validation succeed.
* Required Health checks pass.
* Plugin and Theme failure isolation works.
* Security regression tests pass.
* Critical Admin and public Playwright workflows pass.
* Document 044 integration contracts have no known violations.

---

# 28. Final Acceptance Criteria

* [x] Implementation principles and completion definition defined.
* [x] Phases 0–12 and validation gates defined.
* [x] Milestones A–E defined.
* [x] Module loop, Codex task size, architecture/database change rules, Plugin/Theme gates, performance gate, production gate, documentation freeze, base scope, final rules, and completion criteria defined.

---

# 29. Document Status

This document completes the Favorite CMS base-platform documentation sequence.

Documents 001–045 are the source-of-truth architecture and implementation roadmap for the base CMS.

The next work is bounded implementation of the documented platform, followed later by separate Plugin and Theme specifications for business-specific products.

No additional base architecture document is required before implementation unless a genuine critical gap is discovered and documented deliberately.

---

End of Document

Next Document:

None — Base Platform Documentation Complete
