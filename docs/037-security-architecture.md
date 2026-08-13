# Favorite CMS

Document ID: 037

Title: Security Architecture

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

Next Document:

038-backup-recovery.md

---

# 1. Purpose

This document defines the platform-wide Security Architecture for Favorite CMS.

Security is a cross-cutting property enforced by Core, Engines, Plugins, Themes, Admin, APIs, deployment, and operations.

This document consolidates minimum security boundaries without replacing the detailed contracts of Authentication, Permission, Storage, Database, API, Routing, Logging, Error Handling, and Update systems.

---

# 2. Objectives

Favorite CMS security must prioritize:

* Confidentiality
* Integrity
* Availability
* Least Privilege
* Explicit Trust Boundaries
* Safe Defaults
* Input Validation
* Output Safety
* Plugin and Theme Isolation
* Secret Protection
* Failure-safe Behavior
* Dependency and Update Safety

---

# 3. Trust Boundaries

External clients, browsers, Plugins, Themes, uploaded files, request parameters, configuration sources, third-party services, and network responses must be treated according to explicit trust boundaries.

No component becomes trusted merely because it runs inside the same process.

---

# 4. Authentication and Authorization

The Authentication Engine owns identity verification.

The Permission Engine owns authorization.

Route matching, UI visibility, Resource identifiers, or Authentication success alone must never grant protected access.

---

# 5. Input Validation

All external and cross-component input must be validated by the layer that owns the applicable contract.

Transport validation belongs to API/Routing.

Domain validation belongs to the owning Engine or Plugin.

Client-side validation is never sufficient for protected operations.

---

# 6. Output Safety

Public and Admin outputs must contain only approved data.

Rendering and API layers must not leak internal objects, stack traces, SQL, secrets, filesystem paths, Provider Credentials, or private Plugin state.

---

# 7. Web Content Safety

User-controlled or Plugin-controlled content rendered into HTML must follow an approved escaping or sanitization strategy appropriate to the content type.

Stable structured presentation must remain separate from untrusted markup.

---

# 8. Request Forgery and Cross-Origin Boundary

State-changing browser requests must use an approved protection model appropriate to the Authentication transport.

Cross-origin API access must be explicitly configured.

Production APIs must not default to unrestricted origins for protected operations.

---

# 9. Injection Protection

Database queries must use SQLAlchemy or parameterized query construction.

Routing, templates, file paths, provider adapters, and any command execution must reject untrusted input that could change execution meaning.

Arbitrary code execution from request or configuration input is prohibited unless an explicitly sandboxed contract exists.

---

# 10. File Upload Security

Uploads must be validated by the owning Media or Plugin contract.

Filename, declared content type, size, storage destination, and processing behavior must not be trusted solely from client metadata.

Uploads must not enable path traversal or arbitrary executable placement.

---

# 11. Storage and Database Security

Storage scopes and Providers must remain isolated.

Storage Identifiers do not grant access.

Database Credentials come from secure Configuration and must not be exposed through source code, client bundles, or public diagnostics.

---

# 12. Plugin Security

Plugins must follow manifest validation, dependency checks, lifecycle isolation, Permission contracts, public Engine interfaces, and safe failure behavior.

Plugins must not modify Core, read unrelated secrets, or access another Plugin's private state.

---

# 13. Theme Security

Themes are presentation extensions.

Themes must not access database connections, Storage Provider Credentials, raw Authentication secrets, private backend services, or unrestricted Plugin internals.

---

# 14. Admin Security

Admin is still an untrusted client from the backend perspective.

Protected Admin operations require server-side Authentication and Permission checks.

Sensitive operational tools require explicit authorization.

---

# 15. API and Routing Security

Routing resolves destinations and API coordinates HTTP behavior.

Neither endpoint knowledge nor successful matching grants authorization.

Client values must never select arbitrary private callables.

---

# 16. Secrets

Secrets must be supplied through approved secure Configuration.

They must be excluded from source control, client-side bundles, Logs, Events, Notifications, Error payloads, Theme resources, and ordinary diagnostics.

---

# 17. Logging, Error, and Cache Safety

Logging and Error Handling must minimize sensitive data.

Cache keys and scopes must preserve User, Permission, Locale, Plugin, and protected-resource context.

Protected data must not leak across cache scopes.

---

# 18. Queue and Scheduler Security

Queue Jobs and Scheduled Tasks must use trusted handler registrations.

Client input must not select executable callables directly.

Sensitive Job payloads must be minimized and protected.

---

# 19. Update and Supply-chain Security

Theme, Plugin, and platform updates must validate packages, integrity, compatibility, and dependencies before activation.

Untrusted packages must not execute merely to reveal metadata when safer manifest validation is available.

---

# 20. Dependency and Transport Security

Python, JavaScript, and infrastructure dependencies must be version-managed according to the development workflow.

Production authenticated traffic should use approved secure transport.

Exact TLS, CDN, WAF, and dependency-scanning vendors remain deployment-specific.

---

# 21. Rate and Abuse Protection

Authentication, public APIs, expensive Search, uploads, and other exposed features may require throttling or abuse protection.

Exact thresholds and provider implementation must be defined operationally and must not be invented in generic architecture code.

---

# 22. Data Minimization

The platform should collect, cache, log, and expose only data required for approved functionality.

Diagnostics must not create unnecessary personal-data collection.

---

# 23. Security Failure Behavior

When authorization, secret validation, package validation, or other security-critical checks cannot be completed safely, the platform must default to denial or unavailable behavior rather than uncontrolled access.

---

# 24. Security Testing

Document 040 must test Authentication, Permission denial, input validation, Plugin/Theme isolation, upload/path safety, API protection, secret redaction, update validation, and failure isolation.

---

# 25. Non-Goals

This architecture does not define a fixed role matrix, WAF, secret manager, SIEM, identity provider, TLS vendor, CDN, or rate-limit service.

---

# 26. Codex Security Rules

Codex must:

* Preserve least privilege and explicit ownership.
* Validate untrusted input at the correct boundary.
* Keep public outputs free of sensitive internal data.
* Use SQLAlchemy/parameterized queries.
* Keep secrets out of source code and client bundles.
* Never treat Route matching, UI visibility, or Authentication success as authorization.
* Keep Plugins and Themes isolated.
* Protect uploads and path handling.
* Fail closed for security-critical uncertainty.
* Never invent permissive CORS, rate-limit, role, identity-provider, or secret-provider policies.

---

# 27. Final Acceptance Criteria

* [x] Trust, Authentication, authorization, validation, output, web content, request-forgery, cross-origin, injection, uploads, Storage, Database, Plugin, Theme, Admin, API, Routing, secrets, Logging, Cache, Queue, Scheduler, Update, dependency, transport, abuse, minimization, failure, testing, and Codex rules defined.

---

# 28. Document Status

This document defines the Security Architecture for Favorite CMS.

Security remains a shared platform requirement enforced through the ownership contracts of all Engines and operational systems.

No vendor-specific security provider is required by this architecture.

---

End of Document

Next Document:

038-backup-recovery.md
