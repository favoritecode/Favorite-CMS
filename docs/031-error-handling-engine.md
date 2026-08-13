# Favorite CMS

Document ID: 031

Title: Error Handling Engine

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

Next Document:

032-configuration-engine.md

---

# 1. Purpose

This document defines the architecture, responsibilities, boundaries, and public interfaces of the Favorite CMS Error Handling Engine.

The Error Handling Engine provides a controlled way to classify, normalize, propagate, and safely present failures produced by Core, Engines, Plugins, Themes, background operations, and infrastructure integrations.

It must separate internal diagnostic detail from safe public error results and must not become the owner of business logic, retry execution, rollback policy, Logging, or UI presentation.

---

# 2. Objectives

The Error Handling Engine must provide:

* Normalized Error Records
* Error Identifiers
* Error Categories and Severity
* Error Context and Source
* Controlled Exception Normalization
* Public/Internal Error Separation
* Plugin and Engine Failure Isolation
* API and Rendering Integration
* Retry and Rollback Boundaries
* Logging and Observability Integration
* Security-sensitive Error Protection
* Compatibility and Versioning

No specific exception framework or external error-monitoring provider is required.

---

# 3. Error Record

An Error Record is the normalized representation of one failure.

It may include an Error Identifier, category, severity, source, safe message, approved context, recoverability information, and diagnostic references.

It must not automatically contain raw exception objects, stack traces, Credentials, Tokens, secrets, SQL, private request payloads, or protected business data.

---

# 4. Error Identifier

An Error Identifier is a stable or traceable reference used when correlation is required across API responses, Logs, Queue Jobs, Admin diagnostics, or support workflows.

Consumers must not depend on undocumented identifier formats.

---

# 5. Error Category and Severity

Error Category describes the meaning of a failure, while Error Severity describes operational impact.

Conceptual categories may include validation, Authentication, Permission denial, Resource unavailable, dependency unavailable, conflict, Plugin failure, and internal platform failure.

Exact public codes and severity mappings must be explicitly defined by implementation contracts rather than guessed by individual components.

---

# 6. Error Context and Source

Error Context may include Request Identifier, Route Identifier, Engine Identifier, Plugin Identifier, Job Identifier, operation reference, or a safe User reference.

Every Error Record should identify the component that owns the failing operation when applicable.

Context must remain minimal and must not become unrestricted storage for application state.

---

# 7. Controlled and Unexpected Failures

Controlled failures are expected contract outcomes such as invalid input, denied Permission, or missing Resource.

Unexpected failures are unplanned exceptions or invariant violations.

Both must be normalized safely, but unexpected internal details must not be exposed publicly.

---

# 8. Exception Normalization

Raw exceptions may be converted into Error Records through approved adapters.

Normalization must protect provider-specific messages, SQL, filesystem paths, Credentials, Tokens, secret configuration, private Plugin state, and internal stack details from public exposure.

---

# 9. Public Error Boundary

Public clients must receive only error information approved by the applicable API, Rendering, Admin, or Plugin contract.

Internal diagnostic information and public error information are separate representations.

Public errors must never become accidental diagnostic dumps.

---

# 10. API and Routing Integration

The Routing Engine owns route-resolution failures and returns controlled routing results.

The Error Handling Engine may normalize those failures.

The API Engine owns HTTP-facing error response behavior and status mapping.

The Error Handling Engine must not own a competing API error transport layer.

---

# 11. Rendering Integration

Rendering failures may be normalized and passed back to the Rendering Engine.

The Rendering Engine owns presentation fallback and response composition.

The Error Handling Engine owns normalization and safe diagnostic boundaries.

---

# 12. Authentication and Permission Errors

Authentication failure and Permission denial must remain distinct.

The Authentication Engine owns identity verification failure.

The Permission Engine owns authorization decisions.

Error normalization must not change security meaning or convert denial into success.

---

# 13. Plugin Failure Isolation

A Plugin failure must remain isolated from Core and unrelated Plugins wherever possible.

Plugin errors must identify the Plugin source and must not expose another Plugin's private state.

A broken optional Plugin must not cause the platform to expose raw exceptions.

---

# 14. Queue, Scheduler, Storage, and Database Errors

Queue and Scheduler failures remain owned by their execution systems.

Storage and Database failures remain behind their owning abstractions.

Provider-specific errors, SQL, Credentials, object keys, or private paths must not leak through general Error Records.

---

# 15. Update and Migration Errors

Update and Database Migration failures may require rollback or recovery.

The Update Engine and Database Migration Engine own those decisions.

The Error Handling Engine only normalizes the failure and provides safe diagnostic context.

---

# 16. Logging Integration

Preferred boundary:

Error Source
→ Error Handling Engine
→ Safe Error Record
→ Logging Engine

Logging failure must not replace the original failure or hide the primary business outcome.

---

# 17. Retry and Rollback Boundaries

Retry belongs to the owning Engine, Queue Engine, or another explicit resilience contract.

Rollback belongs to the owning transaction, Update, Migration, or business operation.

The Error Handling Engine must not execute retries or rollback independently.

---

# 18. Fallback Boundary

Fallback behavior may be supported by Rendering, Cache, Storage, Plugin lifecycle, or another owning component.

The Error Handling Engine may describe a failure, but the applicable owner decides whether a fallback is safe and deterministic.

---

# 19. Security

Error handling must protect Credentials, Tokens, secrets, sensitive headers, private User data, protected Resource contents, provider Credentials, internal SQL, and private paths.

When security meaning is uncertain, public output must default to the safer minimal representation.

---

# 20. Failure Isolation

If normalization itself fails, the platform must use a minimal safe fallback Error Record.

One malformed error must not corrupt Logging, API responses, unrelated requests, or the global error pipeline.

---

# 21. Compatibility and Non-Goals

Stable public error contracts must remain compatible across non-breaking versions.

The Error Handling Engine does not own business validation rules, Authentication decisions, Permission decisions, database transactions, Queue retry execution, Scheduler behavior, Update rollback, migration rollback, Logging outputs, or User-facing UI composition.

---

# 22. Final Error Flow

A controlled failure flow is:

1. The owning component detects a failure.
2. The owning component preserves its transaction and business semantics.
3. The failure is normalized into an Error Record.
4. Sensitive internal details are removed from public representations.
5. Approved diagnostic context is attached.
6. Logging or Observability receives safe information when applicable.
7. The applicable API, Rendering, Admin, Queue, or owner converts the error into its contract-specific result.
8. Retry, rollback, fallback, or notification occurs only through the component that owns that policy.

---

# 23. Codex Implementation Rules

Codex must:

* Use normalized Error Records instead of exposing raw exceptions.
* Keep public and internal error representations separate.
* Preserve Authentication and Permission semantics.
* Preserve Plugin isolation.
* Keep retry and rollback outside the Error Handling Engine.
* Integrate with Logging only through approved interfaces.
* Protect Credentials, Tokens, secrets, SQL details, paths, and private payloads.
* Provide a minimal safe fallback when normalization fails.
* Never invent undocumented public error codes, retry rules, or rollback behavior.

---

# 24. Final Acceptance Criteria

* [x] Purpose and objectives defined.
* [x] Error Record, identifier, category, severity, context, and source defined.
* [x] Controlled/unexpected failure and exception normalization defined.
* [x] Public, API, Routing, Rendering, Authentication, Permission, Plugin, Queue, Scheduler, Storage, Database, Update, and Migration boundaries defined.
* [x] Logging, retry, rollback, fallback, security, failure isolation, compatibility, final flow, and Codex rules defined.

---

# 25. Document Status

This document defines the Error Handling Engine specification for Favorite CMS.

The Error Handling Engine remains a cross-cutting normalization and isolation capability. It must not own business logic, retry execution, rollback policy, Logging outputs, or public presentation.

No specific exception library or external error-monitoring provider is required.

---

End of Document

Next Document:

032-configuration-engine.md
