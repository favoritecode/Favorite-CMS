# Favorite CMS

Document ID: 042

Title: Deployment Architecture

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

Next Document:

043-production-operations.md

---

# 1. Purpose

This document defines the deployment architecture for Favorite CMS.

Deployment moves approved backend, frontend, database, Storage, Queue/Scheduler, and Configuration artifacts from local development into production while preserving all platform contracts.

The architecture must support flexible hosting rather than one mandatory provider.

---

# 2. Objectives

Deployment must cover:

* Frontend Deployment
* Backend Deployment
* PostgreSQL Production Database
* Production Storage
* Queue and Scheduler Processes
* Environment Configuration
* Secrets
* Build Artifacts
* Database Migrations
* Health Checks
* Deployment Ordering
* Rollback Boundary
* Scaling Boundary
* Provider-neutral Hosting

---

# 3. Application Components

Production may consist of a Next.js frontend, FastAPI backend, PostgreSQL database, Storage Provider, and Queue/Scheduler worker processes according to enabled capabilities.

These components may be colocated or separated as needed.

---

# 4. Frontend Deployment

The frontend uses Next.js, React, TypeScript, and Tailwind.

It may be deployed to Vercel or another compatible platform.

Frontend builds must never contain backend secrets or direct database Credentials.

---

# 5. Backend Deployment

The backend uses Python and FastAPI.

It may run on a VPS, container host, platform service, or another compatible environment.

The exact application server and process manager remain implementation-specific.

---

# 6. Database Deployment

Production uses PostgreSQL.

Managed or self-hosted PostgreSQL is acceptable when the Database Engine contract is preserved.

Credentials must come from secure Configuration.

---

# 7. Storage Deployment

Production Storage may use Cloudflare R2, another S3-compatible service, or another approved Provider behind the Storage Engine.

Local filesystem storage is suitable for development but must not be assumed durable for every production host.

---

# 8. Queue and Scheduler Deployment

Queue workers and Scheduler processes must use application versions and Configuration compatible with the deployed backend.

Provider selection and process topology remain implementation-specific.

Multiple Scheduler instances require the concurrency protections defined in Document 035.

---

# 9. Configuration and Secrets

Deployment values must be supplied through the Configuration Engine.

Secrets must not be embedded in frontend bundles, repository files, public images, or deployment Logs.

---

# 10. Build Artifacts

Backend and frontend artifacts must correspond to the intended application version.

Plugin and Theme packages must be compatible with that version.

Build systems must not mutate source-of-truth architecture documents.

---

# 11. Database Migrations

Production deployment must run required Migrations through Document 034.

The platform must not serve incompatible code against an unprepared schema.

Migration order relative to activation must follow compatibility rules.

---

# 12. Deployment Order

A safe deployment generally coordinates:

1. Validate release and Configuration.
2. Ensure a recovery point when required.
3. Prepare backend, frontend, and worker artifacts.
4. Run migration preflight and required Migrations.
5. Deploy or activate backend and workers.
6. Deploy or activate frontend assets.
7. Run readiness and smoke checks.
8. Complete traffic cutover only when the target is healthy.

Exact ordering may vary for backward-compatible releases.

---

# 13. Health and Readiness

Deployment automation should use Health/readiness checks before considering a release operational.

A process starting successfully is not sufficient evidence of readiness.

---

# 14. Proxy, CDN, and TLS Boundary

A deployment may use a reverse proxy, CDN, edge cache, load balancer, or TLS terminator.

No specific provider is required.

These layers must not bypass Authentication, API security, cache scope, or canonical Routing contracts.

Production authenticated traffic should use approved secure transport.

---

# 15. Static Assets and Media

Frontend and Theme assets may be served through hosting or CDN infrastructure.

Media delivery must use Media and Storage contracts.

Private Storage Provider paths and Credentials must not be hard-coded into frontend code.

---

# 16. Scaling and State

Backend, worker, Scheduler, Cache, and Storage scaling strategies may differ.

Persistent state belongs in Database, Storage, Queue, Settings, or other approved systems.

Local process memory must not become the sole source of truth when multiple instances are possible.

---

# 17. Environments

Development, test, staging, and production may use different infrastructure while preserving public contracts.

Differences must be expressed through Configuration rather than source-code forks.

---

# 18. Rollback Boundary

Application rollback, Update rollback, Migration recovery, and Backup restore are distinct mechanisms.

A deployment must not promise rollback safety across irreversible schema or data changes.

---

# 19. Failure, Logging, and Backup

A failed deployment must never be marked successful.

Where practical, the previous validated production version should remain available until the target passes readiness checks.

Deployment Logs must protect secrets.

Risky releases may require a verified Backup.

---

# 20. Security and Testing

Production deployment must protect installation endpoints, Admin tools, Health detail, database access, Storage access, and worker infrastructure.

Build, migration, automated tests, and post-deployment smoke validation should block completion on critical failure.

---

# 21. Non-Goals

Deployment does not require Docker, Kubernetes, Vercel for every component, one VPS provider, one CDN, one Queue provider, or one managed PostgreSQL vendor.

---

# 22. Codex Deployment Rules

Codex must:

* Keep frontend, backend, database, Storage, Queue, and Scheduler responsibilities explicit.
* Use PostgreSQL in production.
* Keep secrets in Configuration.
* Run Migrations through Document 034.
* Use readiness, not process start alone, as success evidence.
* Keep hosting provider-neutral.
* Never promise rollback across irreversible Migrations.
* Never hard-code private Storage paths or provider Credentials.

---

# 23. Final Acceptance Criteria

* [x] Frontend, backend, PostgreSQL, Storage, Queue, Scheduler, Configuration, secrets, builds, migrations, deployment order, Health, proxy/CDN, TLS, assets, Media, scaling, state, environments, rollback, failure, Logging, Backup, Security, testing, and Codex rules defined.

---

# 24. Document Status

This document defines provider-neutral deployment architecture for Favorite CMS.

Vercel may host the Next.js frontend, while FastAPI, PostgreSQL, Storage, workers, and Scheduler may run on compatible hosting according to operational needs.

No single hosting vendor is mandatory.

---

End of Document

Next Document:

043-production-operations.md
