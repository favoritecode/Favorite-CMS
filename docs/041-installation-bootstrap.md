# Favorite CMS

Document ID: 041

Title: Installation and Bootstrap

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

Next Document:

042-deployment-architecture.md

---

# 1. Purpose

This document defines Favorite CMS installation and first-run bootstrap architecture.

Installation prepares a new environment for safe startup without requiring manual modification of Core code.

Bootstrap must be repeatable, validation-driven, and safe against partially initialized production state.

---

# 2. Objectives

Installation must coordinate:

* Environment Validation
* Dependency Validation
* Configuration Validation
* Database Initialization
* Database Migrations
* Storage Initialization
* Core Bootstrap
* Engine Registration
* Plugin and Theme Discovery
* Initial Admin Identity
* Default Platform State
* First-run Completion Marker
* Recovery from Partial Installation

---

# 3. Installation State

The platform must distinguish uninstalled, installing, installed, or another explicitly defined state.

Installation state must not be inferred solely from one table or file.

---

# 4. Preflight

Installation preflight should validate the approved Python/Node environment, required Configuration, database connectivity, Storage availability, required write access, runtime dependencies, and application version compatibility.

---

# 5. Configuration

Bootstrap Configuration must be loaded and validated through the Configuration Engine.

Installation must never write secrets into public Settings or client bundles.

---

# 6. Database and Migrations

The Database Engine must establish connectivity.

The Database Migration Engine must initialize or migrate schema to the required version.

Installation must not bypass migration history by silently creating unrelated tables.

---

# 7. Storage Initialization

The Storage Engine must validate required scopes and Provider configuration.

Local development and production object storage may use different adapters behind the same public contract.

---

# 8. Core and Engine Bootstrap

Core must initialize Kernel, Service Container, Configuration, Error Handling, Logging, Database, Storage, required Engines, Routing/API infrastructure, and other approved services in a deterministic order.

Required Engines must validate dependencies before installation is marked complete.

---

# 9. Plugin and Theme Discovery

Installed Plugin and Theme packages may be discovered and validated during bootstrap.

Invalid extensions must not be activated.

Theme required dependencies must follow Theme/Plugin dependency contracts.

---

# 10. Initial Admin Identity

A new installation requires a secure way to establish the first authorized administrative identity.

The process must use User, Authentication, and Permission contracts.

The exact initial role matrix must not be invented by this document.

---

# 11. Credential Safety

Initial Credentials or bootstrap secrets must not be printed into Logs, stored in plaintext documentation, or exposed to public clients.

Temporary bootstrap mechanisms must be invalidated or disabled after setup when applicable.

---

# 12. Default Settings and Locale

Platform defaults may be registered through Settings definitions.

The Default Locale may be selected or validated through Localization and Settings.

Installation must not invent business-specific site configuration.

---

# 13. Installation Lock and Idempotency

Concurrent installation attempts against the same target must be prevented when they can conflict.

Safe installation steps should be repeatable.

Re-running bootstrap must not silently recreate the first Admin identity, reset Settings, or destroy existing data.

---

# 14. Partial Failure and Recovery

If installation fails, the system must record enough state to diagnose and safely retry or recover.

A failed installation must never be marked complete.

Recovery may involve correcting Configuration, re-running unapplied migrations, or repairing Storage without bypassing migration and backup contracts.

---

# 15. Installer Interface Boundary

Installation may be performed through CLI, web setup, automation, or another approved interface.

No one installer UI is required.

Every installer interface must enforce the same backend validation and security rules.

---

# 16. Production Safety

Production deployments must not expose an unrestricted first-run installer after installation completes.

Installation endpoints or bootstrap commands must be disabled, protected, or unavailable according to the implementation.

---

# 17. Logging, Errors, and Health

Installation progress may be logged using safe metadata.

Failures must use the Error Handling Engine.

Before completion, critical Health checks should confirm Database, Storage, migrations, Core services, Authentication path, active Theme, and required Routes are ready.

---

# 18. Testing

Tests must cover clean install, invalid Configuration, database failure, migration failure, Storage failure, repeated bootstrap, partial recovery, and protected post-install state.

---

# 19. Non-Goals

Installation does not define a specific hosting provider, Docker requirement, CLI framework, fixed first-Admin role matrix, or business Plugin sample data.

---

# 20. Final Installation Flow

A clean installation follows:

1. Run environment and dependency preflight.
2. Load and validate bootstrap Configuration.
3. Initialize Error Handling and Logging.
4. Connect to the database.
5. Apply required Migrations.
6. Validate Storage.
7. Bootstrap Core and required Engines.
8. Discover and validate Plugins and Themes.
9. Establish the initial Admin identity.
10. Register approved defaults.
11. Run critical Health checks.
12. Mark installation complete only after all required checks succeed.

---

# 21. Codex Implementation Rules

Codex must:

* Keep installation state explicit.
* Use Configuration, Database, Migration, Storage, User, Authentication, Permission, Theme, Plugin, and Health contracts.
* Never mark partial setup complete.
* Never expose bootstrap secrets.
* Never recreate the first Admin identity on ordinary restart.
* Never bypass migration history.
* Never require one hosting or installer UI.
* Keep repeated bootstrap safe.

---

# 22. Final Acceptance Criteria

* [x] Installation state, preflight, Configuration, Database, Migration, Storage, Core/Engine bootstrap, Plugin/Theme discovery, initial Admin, credential safety, defaults, Locale, locking, idempotency, partial recovery, installer boundary, production safety, Logging, Health, testing, final flow, and Codex rules defined.

---

# 23. Document Status

This document defines installation and bootstrap architecture for Favorite CMS.

A new environment reaches an installed state only after required Configuration, database, migrations, Storage, security bootstrap, Theme, and health validation succeed.

---

End of Document

Next Document:

042-deployment-architecture.md
