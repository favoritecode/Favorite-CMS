# Favorite CMS

Document ID: 044

Title: System Integration Contracts

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

Next Document:

045-implementation-roadmap.md

---

# 1. Purpose

This document is the master system-integration contract for Favorite CMS.

It consolidates ownership, dependency direction, lifecycle, and cross-Engine interaction rules established by Documents 001–043.

Specific owning Engine documents remain authoritative for their detailed behavior.

---

# 2. System Layers

Favorite CMS consists of Core infrastructure, platform Engines, Plugins and Themes, Routing/API interfaces, Rendering/Admin presentation, persistence/infrastructure adapters, and operational systems.

No layer may silently absorb another layer's ownership for convenience.

---

# 3. Core, Engine, Plugin, and Theme Contracts

Core remains business-neutral infrastructure.

An Engine owns one stable platform capability and exposes public interfaces.

Plugins own optional or business-specific functionality and may consume Engine capabilities.

Themes own public presentation and must not own business logic, Authentication, Permission, Database, or Storage Provider access.

---

# 4. Dependency Direction

Preferred dependency direction is:

Core contracts
→ Platform Engines
→ Plugins and Themes
→ Presentation clients

Cross-Engine calls must use public contracts.

Core and required Engines must not depend on optional Plugins.

---

# 5. Service Container

Approved shared contracts may be resolved through the Service Container.

The container must not expose every private implementation indiscriminately.

Only public interfaces intended for cross-component use should be registered.

---

# 6. Startup Lifecycle

Integrated startup follows:

1. Load and validate Configuration.
2. Initialize minimal Error Handling and Logging.
3. Bootstrap Core and Service Container.
4. Initialize Database and required infrastructure.
5. Validate Migration state.
6. Initialize platform Engines.
7. Initialize Storage, Cache, Event, Queue, Scheduler, and related services.
8. Discover and validate Plugins and Themes.
9. Register API and Routing contracts.
10. Activate eligible extensions.
11. Finalize Routes.
12. Run readiness checks.
13. Accept traffic only when required components are ready.

---

# 7. Public Request Flow

Client
→ Routing Engine
→ resolved Route Context
→ Authentication/Permission when required
→ owning Engine or Plugin
→ Render Context
→ Rendering Engine
→ Theme
→ Response

Rendering must never re-own Routing.

---

# 8. API Request Flow

Client
→ Routing Engine
→ resolved API Route Context
→ API Engine
→ request validation
→ Authentication
→ Permission
→ owning Engine or Plugin
→ normalized result
→ API response

API Engine must never maintain a competing global Route registry.

---

# 9. Admin Request Flow

Admin Client
→ Routing/API
→ Authentication
→ Permission
→ owning Engine or Plugin
→ normalized API result
→ Admin presentation

Admin must never access Database or Storage Providers directly.

---

# 10. Content, Media, and Storage

Content Engine owns generic Content lifecycle.

Media Engine owns Media lifecycle and metadata.

Storage Engine owns physical storage abstraction.

Preferred Media path is Media Engine → Storage Engine → Storage Provider.

Themes and Plugins must not bypass these boundaries.

---

# 11. User, Authentication, and Permission

User Engine owns User resources.

Authentication Engine verifies identity.

Permission Engine authorizes actions.

Authentication success never implies authorization.

---

# 12. Settings and Configuration

Configuration Engine owns bootstrap/infrastructure Configuration.

Settings Engine owns application-managed Settings.

User preferences remain User-owned.

Theme customization remains separate from Theme package files.

---

# 13. Routing, API, and Rendering

Routing Engine owns Route registry, matching, conflicts, parameters, and Route Context.

API Engine owns HTTP/API coordination.

Rendering Engine consumes resolved Route Context and owns presentation composition.

No competing Route resolver or Route registry is allowed in API or Rendering.

---

# 14. Event, Queue, and Scheduler

Event Engine coordinates approved Events.

Scheduler decides when work is eligible.

Queue executes asynchronous Jobs.

Owning Engines or Plugins define business behavior.

Scheduler must not duplicate Queue retry.

---

# 15. Logging, Error, and Observability

Error Handling normalizes failures.

Logging records safe operational information.

Observability consumes Health, metrics, correlations, and Logs.

None of these systems independently owns business recovery.

---

# 16. Database and Migration

Database Engine owns connections, sessions, transactions, and SQLAlchemy integration.

Database Migration Engine owns schema evolution and history.

Engines and Plugins own their persisted business data.

---

# 17. Update and Backup

Update Engine owns package validation, compatibility, installation, activation, and rollback where supported.

Migration Engine owns schema changes.

Backup/Recovery may provide recovery points.

Extension Settings and state must be preserved according to their contracts.

---

# 18. Localization, Search, Menu, and SEO

Localization owns Locale/Translation resolution.

Search owns search behavior.

Menu owns navigation structure.

SEO owns SEO metadata resolution.

Themes consume these resources for presentation but do not become their source of truth.

---

# 19. Security and Failure Contract

Every integration must preserve Authentication, Permission, secret, Plugin, Theme, Database, Storage, Cache, and output-safety boundaries.

Optional component failure should remain isolated where safe.

Critical dependency failure must produce controlled unavailable/readiness behavior.

---

# 20. Forbidden Dependencies

The following are forbidden unless future architecture explicitly changes them:

* Core depending on an optional Plugin.
* Theme accessing Database or Storage Provider directly.
* Admin accessing Database directly.
* Rendering owning Route matching.
* API Engine owning a competing Route registry.
* Media Engine owning a competing Storage Provider layer.
* Plugin modifying Core internals.
* Plugin reading another Plugin's private tables or Storage scope.
* Logging/Error Handling controlling business outcomes by itself.
* Scheduler duplicating Queue execution/retry.

---

# 21. Contract Versioning and Testing

Public cross-component contracts must remain stable across non-breaking changes.

Breaking changes require versioning, migration, and tests.

Document 040 must validate the flows and forbidden dependency rules in this document, including the ownership corrections in Documents 011, 013, and 026.

---

# 22. Codex Integration Rules

Codex must:

* Treat Documents 001–044 as source-of-truth contracts.
* Implement one bounded module at a time.
* Use public interfaces for cross-component calls.
* Preserve dependency direction and ownership.
* Never create duplicate infrastructure inside convenience modules.
* Keep optional Plugin failures isolated.
* Add integration tests before declaring cross-system flows complete.
* Never invent undocumented providers, role matrices, Event Names, Route priority algorithms, retry rules, ranking algorithms, or business schemas.

---

# 23. Final Acceptance Criteria

* [x] Core, Engine, Plugin, Theme, dependency direction, Service Container, startup, public/API/Admin flows, Content, Media/Storage, User/Auth/Permission, Settings/Configuration, Routing/API/Rendering, Event/Queue/Scheduler, Logging/Error/Observability, Database/Migration, Update/Backup, Localization/Search/Menu/SEO, Security, failure, forbidden dependencies, versioning, testing, and Codex rules defined.

---

# 24. Document Status

This document defines the master integration contract for Favorite CMS.

It connects the specific Engine documents and makes dependency direction explicit.

Implementation must preserve these integration shapes before the base platform can be considered complete.

---

End of Document

Next Document:

045-implementation-roadmap.md
