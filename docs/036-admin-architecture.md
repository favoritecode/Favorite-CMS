# Favorite CMS

Document ID: 036

Title: Admin Architecture

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

Next Document:

037-security-architecture.md

---

# 1. Purpose

This document defines the Favorite CMS Admin Architecture.

The Admin application is the controlled management interface for platform resources, Engines, Plugins, Themes, configuration surfaces, and operational tools.

It must consume public backend contracts and must never become a privileged shortcut around Engine ownership.

---

# 2. Objectives

The Admin architecture must provide:

* Admin Application Shell
* Authenticated Admin Routing
* Permission-aware Navigation
* Engine Admin Modules
* Plugin Admin Extensions
* Theme and Plugin Management
* Resource Management Surfaces
* Form and Validation Patterns
* API-first Data Access
* Localization
* Safe Error and Notification Presentation
* Operational Diagnostics
* Failure Isolation

The approved frontend stack is React, Next.js, TypeScript, and Tailwind.

---

# 3. Admin Boundary

The Admin application is a client of platform APIs.

It must not access the database, Storage Provider, Queue backend, or private Plugin state directly.

Administrative privilege must still pass through Authentication and Permission contracts.

---

# 4. Admin Shell

The Admin Shell provides shared layout, navigation, Authentication context, Locale context, global notifications, and approved extension points.

It should remain usable when an optional Plugin Admin module fails.

---

# 5. Admin Routing

Admin routes must register through approved Routing contracts.

The Routing Engine owns route registration and matching.

The Admin application owns presentation of the resolved Admin destination.

---

# 6. Authentication and Permission

Admin access requires the Authentication Engine.

Permission-aware UI may hide or disable unavailable actions, but UI visibility is not authorization.

Every protected backend operation must still use the Permission Engine.

---

# 7. Admin Navigation

Admin navigation may be composed from Core, Engines, and Plugins.

Items should declare stable identifiers, destination, owner, order metadata, and Permission requirements.

Plugins must not silently replace unrelated Admin navigation.

---

# 8. Engine Admin Modules

Platform Engines may expose Admin modules through approved contracts.

Examples include Content, Media, Users, Settings, Menus, SEO, Plugins, Themes, Updates, Logs, Health, and other approved management surfaces.

The Admin client must not duplicate backend business rules.

---

# 9. Plugin Admin Extensions

Plugins may register Admin pages, navigation, forms, and components through approved extension points.

A broken Plugin Admin bundle must not crash the Admin Shell.

Plugins must not access another Plugin's private Admin state.

---

# 10. Theme and Plugin Management

Admin may expose Theme and Plugin install, validation, dependency, activation, disablement, configuration, update, and diagnostics.

The Theme Engine, Plugin Engine, and Update Engine remain authoritative for lifecycle decisions.

---

# 11. Content, Media, User, and Settings Surfaces

Content and Media management must use Content and Media APIs.

User and authorization surfaces must use User, Authentication, and Permission contracts.

Settings UI must use the Settings Engine.

Infrastructure Configuration and secrets must not automatically become editable Admin Settings.

---

# 12. Forms and Validation

Client-side validation improves usability but is not authoritative.

Backend Engine or Plugin validation remains the source of truth.

Admin forms must present safe field-level and operation-level error feedback.

---

# 13. API-first Data Access

Admin data access must use the Routing and API Engines through approved HTTP contracts.

The Admin client must not call private backend services or database tables directly.

---

# 14. Client State Boundary

Client state may cache or stage UI data.

Backend Engines remain the source of truth for persistent resources.

The exact frontend state-management library remains implementation-specific.

---

# 15. Localization

Admin UI text must use Localization resources.

User Locale preferences may influence presentation.

Stable identifiers must not be replaced by translated display text.

---

# 16. Errors and Notifications

Admin consumes normalized API errors and approved Notifications.

Raw stack traces, SQL, provider Credentials, secret configuration, and private payloads must not be displayed to Users.

---

# 17. Uploads

Admin upload workflows must use Media or another owning Engine API.

The browser must not receive unrestricted Storage Provider Credentials.

---

# 18. Operational Tools

Authorized Admin tools may expose Update status, Migration status, Scheduler state, Queue diagnostics, Logs, Health, and Backup status.

Each tool must respect the owning subsystem's public contract and Permission checks.

---

# 19. Security

Admin is a high-trust interface but remains an untrusted client from the backend perspective.

All Admin input must be validated.

Sensitive operations require server-side Authentication and Permission evaluation.

---

# 20. Accessibility and Performance

Admin interfaces should use semantic, keyboard-compatible, responsive UI patterns where practical.

Performance should use pagination, filtering, caching, and deferred loading when supported without bypassing security or ownership.

---

# 21. Failure Isolation and Testing

A failed optional Admin module must not prevent access to unrelated recovery tools.

Document 040 must cover login, Permission denial, Content/Media management, Plugin/Theme lifecycle, diagnostics, and controlled Plugin Admin failure with Playwright.

---

# 22. Non-Goals

The Admin architecture does not own backend business logic, database persistence, Authentication policy, Permission policy, public Theme rendering, Storage Provider operations, or Queue worker execution.

---

# 23. Final Admin Flow

A protected Admin operation follows:

1. Resolve the Admin route.
2. Resolve Authentication Context.
3. Render Permission-aware navigation and page shell.
4. Request data through the API Engine.
5. Backend Permission Engine authorizes the operation.
6. The owning Engine or Plugin performs validation and state changes.
7. Return a normalized API result.
8. Admin presents success or safe error information.

---

# 24. Codex Implementation Rules

Codex must:

* Use React, Next.js, TypeScript, and Tailwind.
* Treat Admin as an API client.
* Preserve server-side Permission enforcement.
* Keep public Theme presentation separate from the Admin Shell.
* Use approved Plugin Admin extension points.
* Keep Plugin failures isolated.
* Never expose secrets, raw stack traces, database details, or Storage Provider Credentials.
* Never duplicate backend business rules in frontend code.

---

# 25. Final Acceptance Criteria

* [x] Admin shell, routing, Authentication, Permission-aware UI, navigation, Engine/Plugin modules, Theme/Plugin management, resource surfaces, forms, API, localization, errors, uploads, operational tools, Security, accessibility, performance, failure isolation, testing, final flow, and Codex rules defined.

---

# 26. Document Status

This document defines the Admin Architecture for Favorite CMS.

The Admin application is a secure API-first management client built with React, Next.js, TypeScript, and Tailwind.

It must never bypass backend Engine ownership, Authentication, Permission, Routing, API, Database, or Storage boundaries.

---

End of Document

Next Document:

037-security-architecture.md
