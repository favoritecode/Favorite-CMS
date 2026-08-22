# Favorite CMS implementation status

This file records implementation progress without changing the architecture contracts in Documents 001–045.

## Phase 0 — Repository Baseline

Status: Complete

Implemented:

- Documented monorepo boundaries for backend, frontend, plugins, themes, runtime storage, tests, scripts, tools, resources, documentation, and repository automation.
- Business-neutral FastAPI application factory and startup endpoint.
- Next.js App Router skeleton using React, TypeScript, and Tailwind CSS.
- Backend Pytest smoke test and frontend Playwright smoke test.
- Environment template, Git-safe ignore rules, local setup commands, and containerized development workflow.

Validation:

- Backend Pytest: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Playwright assertion: passed; the local command runner retained the spawned Next.js process until its outer timeout on Windows.

Architecture review:

- No business-specific functionality was added.
- Frontend contains presentation only.
- Plugin and Theme roots are empty extension boundaries.
- Runtime data and secrets are ignored.

Open documentation issue:

- Documents 001–045 do not define project license terms. `LICENSE` therefore records that no license grant is specified; no license model was invented.

## Phase 1 — Core Runtime

Status: Complete

Implemented:

- Business-neutral Kernel, explicit Service Container, deterministic Engine Manager, lifecycle startup/shutdown, readiness, and controlled startup failure.
- Typed Configuration Engine with explicit sources, unique-priority precedence, schema validation, approved environment mapping, protected secret values, and non-sensitive snapshots.
- Provider-neutral structured Logging Engine with controlled levels/categories/sources, allow-listed context, correlation fields, filtering, secret protection, and isolated outputs.
- Error Handling Engine with controlled/unexpected normalization, separate internal/public records, minimal approved context, secret-safe output, and fallback normalization.
- Generic Extension System foundation with Theme/Plugin identity, required manifest fields, version/compatibility validation, dependency declarations, cycle checks, manifest-only discovery, controlled activation/deactivation, documented states, and failure isolation.
- FastAPI lifespan integrated with the Phase 1 Core bootstrap and shutdown lifecycle.

Validation:

- Backend Pytest: 37 passed.
- Python bytecode compilation: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Playwright assertion: passed; the local Windows command runner retained the spawned development process until its outer timeout.

Architecture review:

- Only public Phase 1 contracts are registered in the Service Container.
- Configuration remains separate from future Settings.
- Logging and Error Handling do not own business recovery.
- Extension discovery parses validated manifests and performs no dynamic imports or code execution.
- No Phase 2 or later Engine and no business Plugin functionality was added.

## Phase 2 — Persistence Foundation

Status: Complete

Implemented:

- SQLAlchemy Database Engine with Configuration-owned connection URLs, SQLite and PostgreSQL provider validation, connection checks, explicit sessions, owner-controlled transactions, rollback, safe failures, readiness, and disposal.
- Database Migration Engine with explicit registration, owner metadata, deterministic dependency ordering, provider compatibility, explicit history initialization, database-backed locking, transactional upgrades where supported, successful-only version tracking, and controlled failures.
- Provider-neutral Storage Engine with normalized references, explicit owner scopes, local development provider, store/retrieve/exists/delete/copy/move/metadata operations, safe move behavior, path validation, traversal prevention, scope isolation, and controlled provider failures.
- Optional Cache Engine with provider abstraction, in-memory development provider, scoped keys, hits/misses, set/get/exists/delete, TTL, scope clearing, and fail-open degradation to cache misses or explicit unsuccessful mutation results.
- Core lifecycle registration and deterministic startup/shutdown for Database, Migration, Storage, and Cache Engines.

Validation:

- Backend Pytest: 68 passed.
- Python bytecode compilation: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Playwright assertion: passed in 501 ms; the local Windows command runner retained the spawned development process until its outer timeout.
- SQLite connection, sessions, commit, rollback, file creation, migration history, locking, and repeated upgrades: passed.
- PostgreSQL configuration and driver path: implemented; live PostgreSQL integration was not run because no test server is configured.

Architecture review:

- Database owns only SQLAlchemy connectivity, sessions, and transactions; no business models or tables were added.
- Migration owns explicit schema history and execution; application startup performs no schema creation or upgrade.
- Storage owns physical storage and scopes; no Media Engine behavior was added.
- Cache remains temporary acceleration and degrades without affecting source-resource truth.
- Configuration, Logging, Error Handling, and Core ownership remain unchanged.
- No Phase 3 or later Engine and no business functionality was added.

## Phase 3 — Messaging and Background Infrastructure

Status: Complete

Documents implemented:

- `018-event-engine.md`
- `019-queue-engine.md`
- `035-scheduler-engine.md`
- `020-notification-engine.md`

Implemented:

- Generic Event Engine with explicit contracts, stable identities, validated payloads, approved publishers, ordered subscriptions, synchronous dispatch, listener isolation, safe failure records, unsubscribe support, lifecycle control, and nested synchronous publication protection. It claims no persistence, retry, asynchronous delivery, or global ordering guarantee.
- Provider-neutral Queue Engine with explicit Job contracts, normalized identities/status/results, validated payloads, in-memory development provider, enqueue/dequeue/acknowledgement/failure, immediate and delayed availability, explicit contract-owned retry limits, cancellation, isolated execution, and caller-driven Worker lifecycle. It claims no persistence, exactly-once delivery, distributed ordering, or automatic idempotency.
- UTC/time-zone-aware Scheduler Engine with one-time and interval definitions, explicit owner/state/missed-run policy, deterministic eligibility, duplicate concurrent-dispatch protection, Plugin-owner availability boundary, Queue-only deferred dispatch, cancellation/removal boundaries, and failure isolation. It performs no Queue execution or Queue retry.
- Provider-neutral Notification Engine with explicit contracts, recipients, channels, validated payloads, delivery adapters, pending/delivered/failed state, recipient isolation, safe failures, development memory adapter, successful-delivery duplicate protection, and optional deferred delivery through an explicitly registered Queue Job contract.
- Core lifecycle registration and deterministic startup/shutdown for Event, Queue, Notification, and Scheduler Engines.

Validation:

- Backend Pytest: 94 passed.
- Python bytecode compilation: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Playwright assertion: passed in 450 ms; the local Windows command runner retained the spawned development process until its outer timeout.
- No external broker, scheduler, messaging, or notification provider was required or tested.

Architecture review:

- Events communicate occurrences and do not execute Queue work automatically.
- Queue owns deferred Job execution and explicit retry; no business Job types exist in production registration.
- Scheduler decides when Queue work is eligible and contains no worker or retry implementation.
- Notification owns coordination/delivery state; adapters own transport and Queue owns deferred execution when explicitly configured.
- No new database, transaction, storage, cache, configuration, logging, or error infrastructure was created.
- No Phase 4 or later Engine and no business-specific workflow was added.

## Phase 4 — Identity and Security

Status: Complete

Documents implemented:

- `015-user-engine.md`
- `025-authentication-engine.md`
- `016-permission-engine.md`
- Phase-applicable requirements from `037-security-architecture.md`

Implemented:

- User Engine with stable UUID identity, normalized unique email identity, approved profile data, explicit role reference, Active/Inactive/Restricted account states, safe public representation, isolated updates, SQLAlchemy persistence, and an explicit owned migration.
- Authentication Engine with centralized salted PBKDF2-HMAC-SHA256 password hashing, email/password verification, HS256 JWT contexts, fixed issuer/algorithm validation, expiration, persisted context revocation, logout, password-change credential-version invalidation, account-state enforcement, safe anonymous failure, bounded credential/token input, and protected credential representations.
- Permission Engine with explicit capability registration, owner-scoped role grants, optional capability-specific ownership/public rules, deterministic decisions, default deny, and no built-in role matrix or superuser bypass.
- Permission consumes only Authentication Engine-issued integrity-checked contexts and resolves current roles through User Engine; caller-supplied authentication or role claims cannot grant access.
- Production requires Configuration-supplied JWT signing material; development/test may use an ephemeral process-only key. Secrets remain excluded from configuration snapshots, Logs, Errors, Events, Notifications, and public User output.
- Core lifecycle registration and deterministic shutdown for User, Authentication, and Permission Engines. No API routes or Admin/frontend authentication UI were introduced.

Validation:

- Backend Pytest: 117 passed.
- Python bytecode compilation: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Playwright assertion: passed in 459 ms; the local Windows command runner retained the spawned development process until its 60-second outer timeout.
- Repository security searches found direct environment access only in Configuration, no duplicate Authentication/Permission implementation, no credential logging/serialization path, and schema creation only inside explicit Migration contracts and migration tests.
- The formal Codex Security scan backend was not exposed in this task, so no generated scanner report is claimed.

Architecture review:

- User owns User Resources, Authentication owns identity verification and credential context, and Permission owns authorization decisions.
- Authentication success alone grants no capability; unknown permissions, roles, invalid/forged contexts, and unavailable authorization state deny.
- User and Authentication tables are registered through Database Migration Engine and are never created or altered by application startup.
- Database, Migration, Event, Notification, Core, Configuration, Logging, Error Handling, and Extension ownership remain unchanged.
- No Phase 5 or later Engine, API/Admin surface, business permission matrix, external identity provider, or business workflow was added.

## Phase 5 — Platform Data Engines

Status: Complete

Documents implemented:

- `021-settings-engine.md`
- `012-content-engine.md`
- `013-media-engine.md`
- `014-search-engine.md`
- `028-localization-engine.md`
- `022-menu-engine.md`
- `023-seo-engine.md`

Implemented:

- Settings Engine with explicit definitions, typed JSON values, isolated Platform/Engine/Theme/Plugin/User scopes, defaults, updates, reset, definition removal with stored-value preservation, protected values, Permission integration, Cache invalidation, and explicit migration.
- Content Engine with contract-registered generic Content Types, typed fields, Draft/Published/Archived lifecycle, create/read/query/update/delete/publish/archive operations, owner and public Permission checks, deterministic pagination, Cache invalidation, and explicit migration.
- Media Engine with Image/Video/Audio/Document Resources, metadata, scoped Storage-only byte operations, access-contract registration, upload/read/update/delete, provider-neutral processing registration, normalized delivery references, failure preservation, and explicit migration.
- Search Engine with registered resource contracts, rebuildable derivative in-memory index, normalization, registered filters, deterministic title/resource ordering, pagination, live search, source visibility rechecks, protected-result filtering, invalidation/removal, and failure isolation. No ranking algorithm or vendor was introduced.
- Localization Engine with Language/Locale registration, caller-defined locale precedence, explicit default Locale, namespaced Translation Resources, caller-defined fallback chains, conflicts, updates, missing-result handling, and namespace isolation.
- Menu Engine with persistent Menus, Items, Locations, assignments, hierarchy validation, deterministic ordering, destination registration/availability isolation, permission-aware visibility, item/menu removal, and explicit migration. It contains no Routing or presentation implementation.
- SEO Engine with persistent source contributions, documented precedence, approved resource-type ownership, source-of-truth visibility callbacks, safe canonical validation, update/removal, fallback resolution, private-resource suppression, and explicit migration. It contains no Routing, Rendering, or external SEO service.
- Core lifecycle registration and deterministic shutdown for all seven Phase 5 Engines.

Validation:

- Backend Pytest: 137 passed.
- Python bytecode compilation: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Playwright assertion: passed in 638 ms; the local Windows command runner retained the spawned development process until its 60-second outer timeout.
- Security searches found environment reads only in Configuration, physical filesystem operations only in Storage, and Phase 5 schema creation only inside explicit Migration contracts.

Architecture review:

- Content owns generic content lifecycle; no business Content Types exist in production registration.
- Media owns logical Media Resources and metadata while Storage exclusively owns physical storage and Providers.
- Search is derivative and clears its process-local index at shutdown; source Engines remain authoritative.
- Settings remains application-managed data and does not read environment or replace Configuration.
- Localization, Menu, and SEO expose structured data contracts without taking ownership of Rendering, Routing, Theme, or Plugin behavior.
- Authorization uses existing Permission contracts; no permission matrix, Event Names, locale precedence, fallback chain, search ranking algorithm, or provider was invented.
- No Phase 6 or later Engine, API/Admin surface, business workflow, or industry-specific schema was added.

## Phase 6 â€” Extension Runtime

Status: Complete

Documents implemented:

- `008-extension-system.md`
- `010-plugin-engine.md`
- `009-theme-engine.md`

Implemented:

- Completed the generic Extension lifecycle with immutable permission declarations, deterministic dependency ordering, cycle/version/missing-dependency validation, explicit runtime attachment, registration/activation/deactivation boundaries, reverse shutdown ordering, uninstall state, and atomic replacement with rollback.
- Plugin Engine with manifest-only discovery, explicit host runtime binding, permission-grant validation, an allowlisted public-service context, deterministic dependency activation, failure isolation, safe deactivation, shutdown, and rollback on failed replacement. Installed files never trigger dynamic imports.
- Theme Engine with manifest-only discovery, explicit package/runtime binding, safe package-relative template/layout/component/asset validation, traversal and symlink rejection, one active Theme, atomic Theme switching with prior-Theme restoration, safe shutdown, and rollback on invalid/failed updates.
- Theme Settings remain owned by the external Settings Engine and are never stored in or deleted with Theme package files.
- Core lifecycle registration after the completed platform Engines. No Routing, API, Rendering, Admin, update-package installer, or business extension was added.

Validation:

- Backend Pytest: 144 passed.
- Python bytecode compilation: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Playwright smoke test: passed.
- Security searches found no dynamic import/eval/exec path in Extension, Plugin, or Theme code, and no direct environment, Database, or Storage Provider access in Theme code.

Architecture review:

- Core owns composition while Extension System owns generic contracts/lifecycle, Plugin Engine owns Plugin-specific hosting, and Theme Engine owns Theme packages/presentation resources only.
- Plugin runtimes receive only explicitly allowlisted public Engine services; Configuration secrets and private Database/Storage Provider implementations are not exposed.
- Theme resource discovery does not render, resolve Routes, access Database, or access Storage Providers.
- Python extension runtimes are explicitly trusted host registrations; no sandbox guarantee is claimed because Documents 008â€“010 define no enforceable Python sandbox or executable manifest entrypoint.
- Invalid, duplicate, incompatible, dependency-broken, and activation-broken optional extensions fail without preventing unrelated extension operation.

## Phase 7 — Routing, API, and Rendering

Status: Complete

Documents implemented:

- `029-routing-engine.md`
- `026-api-engine.md`
- `011-rendering-engine.md`

Implemented:

- Routing Engine as the sole owner of active Route registration, discovery, conflict detection, method-aware deterministic matching, declared parameter extraction, owner-controlled activation/removal, navigation-path construction, and immutable Route Context creation.
- Structurally overlapping Routes for the same method are rejected rather than resolved using an undocumented priority algorithm. API contract versions remain explicit opaque values; no undocumented version negotiation was introduced.
- API Engine with operation contracts (not a Route registry), transport validation, approved header/query/body normalization, existing Authentication and Permission integration, owner dispatch, public-value serialization, prohibited-field filtering, deterministic status/error normalization, request identifiers, and safe unexpected-failure handling.
- Rendering Engine consuming pre-resolved Route Context, active Theme packages, explicit presentation operations, declared Theme resources, deterministic Theme → Plugin → Platform fallback, stable priority/tie-breaking, template/layout/component/widget composition, optional resource isolation, logical asset references, and safe response construction.
- FastAPI is a transport adapter over Routing → API/Rendering and no longer owns parallel business Routes. Framework documentation endpoints are disabled until explicitly registered through the platform contracts.
- Plugin-scoped Routing/API/Rendering facades enforce Plugin ownership. Plugin activation failure or deactivation removes Plugin-owned Phase 7 registrations. Themes receive no backend Route registration interface.

Request flow:

- API: HTTP client → FastAPI transport → Routing Engine → immutable API Route Context → API Engine validation → Authentication → Permission → registered owning operation → explicit serializer → normalized JSON response.
- Presentation: HTTP client → FastAPI transport → Routing Engine → immutable presentation Route Context → Authentication/Permission when declared → owning resource resolver → Rendering Engine → active Theme/resource fallback → response.

Validation:

- Backend Pytest: 158 passed.
- Python bytecode compilation: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Frontend production build: passed.
- Playwright browser assertion: passed; the Windows runner retained its development-server child process until the outer timeout.
- Source-backed security review found no duplicate route registry, dynamic client-selected handlers, raw ORM serialization, direct Database/Storage access, token logging, unsafe redirects, or Theme backend-service access in Phase 7 code.
- The formal Codex Security desktop scan could not be started because its required scan-start capability was unavailable; no generated scanner artifact is claimed.

Architecture review:

- Routing alone owns Route matching and Route Context. API coordinates HTTP without `_routes`; Rendering has no Route resolver or Routing registry reference.
- Authentication verifies credentials, Permission authorizes, and both API and protected presentation flows fail closed before invoking the registered owner operation.
- Content/Media/Localization/Menu/SEO remain source owners and can be consumed only through registered operation/resource resolvers; Rendering and API add no domain persistence.
- Theme owns package identity/resources/lifecycle while Rendering validates declared logical package references and performs composition without exposing package paths.
- No Admin, Update, Backup, Observability, deployment, business Route, business schema, or industry-specific workflow was added.

## Phase 8 — Admin Application

Status: Complete

Document implemented:

- `036-admin-architecture.md`

Implemented:

- API-first Admin application contract with authenticated login/logout, server-authorized permission-aware module discovery, deterministic navigation ordering, owner-scoped module registration, and optional Plugin Admin module isolation.
- No administrator role, superuser bypass, default grants, or permission matrix was invented. Owning Engines and Plugins must explicitly define management permissions and operations before their modules become visible.
- Next.js/React/TypeScript/Tailwind Admin shell with accessible login form, responsive navigation, dashboard, loading/empty/error states, safe messages, and logout.
- Next.js server-only Authentication bridge stores the existing backend credential in an HttpOnly, SameSite=Strict cookie. Tokens are not stored in localStorage/sessionStorage or exposed to client components. Logout revokes the Authentication context before clearing the cookie.
- Admin module links use only validated `/admin/...` destinations. The backend remains authoritative; hiding navigation never grants or replaces Permission checks.
- Plugin Admin extensions receive an owner-scoped facade. Invalid ownership fails activation, and Plugin deactivation removes its Admin modules without affecting the shell or unrelated modules.
- Update, Backup, Health, deployment, and other later-phase operational modules were not registered. No business modules, demo Plugins, or demo Themes were introduced.

Validation:

- Backend Pytest: 164 passed.
- Python bytecode compilation: passed.
- Frontend ESLint: passed.
- Frontend TypeScript check: passed.
- Next.js production build: passed, including `/admin`, `/admin/login`, and server session/module proxy routes.
- Playwright: three browser assertions passed after correcting a timing-sensitive test; on Windows the development-server child process continued until the outer command timeout.
- Security searches found no browser-readable credential storage, raw HTML rendering, direct Admin Database/Storage access, permissive CORS, unsafe redirect, or client-bundled secret.

Architecture review:

- Admin is a presentation/API client. Routing, API, Authentication, Permission, User, Content, Media, Settings, Localization, Menu, SEO, Plugin, and Theme ownership remains unchanged.
- Admin has no SQLAlchemy, Database, Storage Provider, Cache Provider, Queue backend, filesystem, or private Engine access.
- Management operations remain API operation contracts owned and validated by the applicable Engine or Plugin; Admin adds no duplicate CRUD persistence.
- Formal Codex Security scanning remains unavailable in this desktop session, so no generated scanner report is claimed; backend security regressions and source audits passed.
- No Phase 9 or later Engine was implemented.

## Phase 9 — Update and Recovery

Status: Complete

Documents implemented:

- `024-update-engine.md`
- `038-backup-recovery.md`

Implemented:

- Update Engine with explicit validation, SHA-256 package integrity, Core/version/dependency compatibility through existing Extension contracts, downgrade/reinstall protection, scoped Storage staging, per-target concurrency locking, persistent versioned update history, explicit Migration Engine coordination, Plugin/Theme activation, post-activation version validation, cleanup, and prior-version rollback through the existing atomic extension replacement contracts.
- The Update state model is Pending → Validating → Prepared → Installing → Activating → Completed. Validation or activation failure without migrations transitions through Rolling Back → Rolled Back; migration failure transitions to Failed because irreversible migration rollback is not claimed.
- Backup/Recovery Engine with explicit backup scopes, provider-neutral protected Storage destination, consistent SQLite database snapshots owned by Database Engine, scoped Storage resources, Settings through the database-owned snapshot, Plugin/Theme version and lifecycle state, self-describing metadata, deterministic serialization, SHA-256 verification, restart discovery, compatibility validation, restore preflight, and best-effort restoration of the pre-restore database/storage state when activation fails.
- Database Engine owns SQLite snapshot creation, integrity validation, and restore. Non-SQLite providers fail closed behind the same boundary; no PostgreSQL backup tool or live PostgreSQL validation is claimed.
- No remote update source, archive extraction, executable manifest entrypoint, signature scheme, marketplace, retention policy, scheduler, deployment, or Admin/API operation was invented. Trusted runtime/package candidates are supplied explicitly to existing Plugin/Theme contracts and discovery never executes package code.

Validation:

- Phase 9 Pytest: 7 passed.
- Full backend Pytest: 171 passed.
- Python bytecode compilation: passed.
- Frontend ESLint, TypeScript, production build, and Playwright validation: passed as recorded in the Phase 9 completion report.
- Source searches investigated dynamic execution, subprocess/command execution, direct environment access, schema creation, and filesystem access. Phase 9 adds no eval/exec/subprocess/system call, environment access, archive extraction, arbitrary import, or direct update-package filesystem mutation.

Architecture review:

- Update coordinates existing Migration, Storage, Plugin, and Theme public contracts; it does not replace their ownership.
- Recovery coordinates Database-owned snapshots and scoped Storage resources. Backup/restore remains distinct from Update rollback and Migration failure handling.
- Configuration secrets do not enter backup metadata or update history. Update failure records contain normalized failure categories rather than raw exceptions or paths.
- No Phase 10 Observability, Health, installation, deployment, production operations, or business functionality was added.

## Phase 10 — Operational Readiness

Status: Complete

Documents implemented:

- `039-observability-health.md`
- `041-installation-bootstrap.md`
- `042-deployment-architecture.md`
- `043-production-operations.md`

Implemented:

- Central Observability/Health Engine with centrally defined healthy, degraded, and unavailable states; distinct lightweight liveness and dependency-derived readiness; Database, Migration, Storage, Cache, Queue, Scheduler, Authentication, and active-Theme checks; isolated optional/critical contributors; owner cleanup; and minimal topology-free `/health/live` and `/health/ready` API contracts registered through Routing/API.
- Explicit installation state persisted by migration `platform.installation.001`, installation locking, preflight, explicit migration execution, Storage validation, caller-defined initial identity role and authorization requirements, secure Authentication provisioning, active-Theme/readiness validation, failed-state recording, partial retry, and installed-state idempotency. No role matrix, default Theme, installer UI, or bootstrap secret is invented.
- Provider-neutral production deployment validation for production environment, disabled debug mode, PostgreSQL, non-local approved Storage, non-empty Authentication secret, complete migrations, and readiness. It validates only and performs no hosting or deployment mutation.
- Provider-neutral deployment and production-operations runbooks covering release ordering, migrations, recovery points, readiness cutover, Update, Backup/Restore, Database, Storage, Queue/Scheduler, Plugin/Theme failure, incidents, and credential rotation without vendors, thresholds, retention, or deployment orchestration.

Validation:

- Phase 10 Pytest: 10 passed.
- Full backend Pytest: 181 passed.
- Public Health output contains only normalized status and live/ready booleans; detailed component topology remains internal to approved diagnostics consumers.
- Security source searches found no Phase 10 eval/exec, subprocess, command execution, dynamic import, unsafe deserialization, direct environment read, arbitrary filesystem access, duplicate registry, raw exception output, or client-selected callable. Schema creation appears only inside the registered installation Migration callback; Storage filesystem access remains inside Storage Engine.
- Formal Codex Security scan startup capability was unavailable in this desktop tool surface, so no generated scanner report is claimed.

Architecture review:

- Observability consumes owning Engine health contracts and never controls business outcomes, Logging, Queue work, Backup policy, or alerting.
- Installation coordinates Configuration-established Core, Migration, Storage, User, Authentication, Permission, Theme, Plugin, and Health public contracts. Ordinary application startup does not automatically install or migrate.
- Deployment and operations validation preserve Update, Recovery, Migration, Storage, Plugin, Theme, Queue, Scheduler, Configuration, Routing, and API ownership.
- No Phase 11 full-testing expansion, Phase 12 freeze work, business feature, vendor integration, deployment automation, monitoring vendor, or undocumented Admin module was added.

## Phase 11 — Full Testing Gate

Status: Failed — required browser coverage is incomplete

Authoritative documents:

- `040-testing-strategy.md` (the repository contains no `040-full-testing-gate.md`)
- `044-system-integration-contracts.md`
- `045-implementation-roadmap.md`

Completed verification:

- Added regression gates proving ordinary startup performs no schema mutation, Routing alone owns its Route registry, API owns no competing Route registry, Rendering owns no Route resolver, Media owns no Storage Provider abstraction, and verified Backup restore recovers compatible Extension lifecycle state.
- Phase 11 focused Pytest: 3 passed.
- Full backend Pytest: 184 passed.
- Python compilation, frontend lint, TypeScript, and production build passed.
- Existing Playwright suite: 3 assertions passed; Windows retained the development-server child process until the outer timeout.
- Security searches reviewed dynamic execution, subprocess/commands, deserialization, environment reads, schema mutation, filesystem access, client storage/raw HTML/redirects, secrets, and duplicate ownership. Matches were confined to documented owners: Configuration environment reads, Migration callbacks/schema infrastructure, Database snapshot temporary files, Storage provider filesystem access, and Theme/Media path validation.
- SQLite Database, Migration, Storage, Update, Backup/Restore, Installation, and Health gates passed. PostgreSQL live behavior was not executed because Docker and an approved PostgreSQL server are unavailable; PostgreSQL configuration and controlled connection-failure behavior remain covered.

Release-gate deficiency:

- Document 040 section 13 requires Playwright coverage for Admin Permission denial, Content/Media flows, Settings, Plugin/Theme management, diagnostics, public Routing/Rendering, Search, Localization, missing Resources, and graceful Plugin/Theme failure.
- The current Playwright suite covers the public shell, Admin login/logout, permission-filtered navigation, loading, empty, and safe error states only. The remaining required browser workflows are absent. Mock-only assertions would not validate the required end-to-end Engine flows, and implementing missing management UI/API workflows is outside Phase 11 scope.

Phase 11 gate: FAIL. Phase 12 was not started.

Phase 11 browser-gate continuation:

- Re-audit confirmed the former Admin Playwright tests intercepted the Next.js session/module endpoints and therefore did not constitute the real Browser → Next.js → FastAPI → Routing/API → Authentication/Permission flow required by Document 040.
- Added a deterministic test-only application seed using public Migration, User, Authentication, Permission, and Admin contracts, and configured Playwright to start both the real FastAPI transport and Next.js application.
- Replaced intercepted Admin tests with real unauthenticated denial, authenticated explicitly authorized navigation, authenticated-but-unauthorized empty navigation, HttpOnly/SameSite cookie checks, no browser-storage credentials, invalid-credential safe errors, logout revocation, and post-logout denial.
- Found and fixed a real session defect: logout revoked the backend credential but did not expire the browser cookie with the same `/admin` path. Cookie expiry now uses the original path and security attributes.
- Playwright: 5 real browser assertions passed. The Windows development-server teardown still retained child processes until the outer timeout.
- The public home assertion remains frontend-only. No production public Rendering Route, Content/Media/Settings management pages, Plugin/Theme management pages, diagnostics page, Search/Localization UI, or graceful extension-failure UI exists to exercise through the required real browser flow.
- Mandatory Document 040 section 13 workflows therefore remain incomplete. Phase 11 remains FAIL and Phase 12 remains unstarted.

Phase 11 browser-gate completion:

- Added the minimum generic production management/public surfaces authorized for the testing gate. Admin remains a credential-forwarding API client; `AdminPlatformEngine` coordinates explicit Routing/API operations while Content, Media, Settings, Search, Localization, Plugin, Theme, Health, and Rendering retain ownership.
- Added explicit default-deny management permissions for Content, Media, Settings, Extensions, and Diagnostics. No role or grant is installed by production composition; the local E2E fixture grants only its synthetic operator role.
- Real Playwright coverage now exercises Content list/create and validation, Media upload through Media → Storage, Settings read/update, Plugin activation and isolated activation failure, Theme activation failure with the previous active Theme still rendering, liveness/readiness diagnostics, public Routing → resolved Route Context → Rendering → active Theme, Search visibility and empty behavior, Localization fallback and missing translation, safe missing public resources, Admin authentication/denial/logout, credential-storage safety, safe errors, and safe destinations.
- The E2E fixture seeds synthetic data and extensions exclusively through Migration, User, Authentication, Permission, Content, Media, Settings, Search, Localization, Plugin, and Theme public contracts. It does not use direct SQL, Storage providers, mocked HTTP, remote services, or dynamic package loading.
- Full backend Pytest: 184 passed. Authentication regression testing exposed and fixed acceptance of non-canonical base64url credential encodings; the unchanged tamper test and full suite now pass.
- Frontend ESLint, TypeScript, and production build passed. Playwright: 8/8 real browser assertions passed. The outer command still timed out after assertion completion because the known Windows development-server child process remained alive.
- Formal Codex Security scan startup remains unavailable in this tool surface; local source/diff security checks were performed and no new critical ownership or exposure issue was found.

Phase 11 gate: PASS. Phase 12 was not started.

## Phase 12 — Integration Freeze

Status: Complete

Authoritative scope:

- `044-system-integration-contracts.md`
- Section 16 of `045-implementation-roadmap.md`
- No dedicated Phase 12 component document exists in the repository.

Implemented validation:

- Added executable integration-freeze guards for forbidden cross-layer imports: Core cannot depend on optional Plugin/Theme Engines; Admin cannot import Database, SQLAlchemy, or Storage; Theme cannot import Database, Storage, Authentication, or Permission implementations.
- Added corrected-ownership guards proving Routing alone owns Route storage/resolution, API has no competing Route registry/resolver, Rendering has no Route resolver, Media has no competing Storage Provider abstraction, and Scheduler delegates execution without owning Queue workers.
- Added Admin boundary guards preventing schema creation, direct environment access, SQLAlchemy access, or Storage Provider access.
- Added deterministic composition verification across independent Kernels, including stable Engine ordering, unique Engine identities, and distinct Routing/API services.
- No Engine, API, Route, permission, migration, persistence, provider, UI, or business behavior was added for Phase 12.

Validation:

- Phase 12 focused Pytest: 4 passed.
- Full backend Pytest: 188 passed.
- Python compilation, frontend ESLint, TypeScript, and production build: passed.
- Playwright browser assertions: 8/8 passed through real FastAPI and Next.js transports. The outer command retained the known Windows development-server child process and timed out only after all assertions completed.
- Source audit found no eval/exec, subprocess/system execution, arbitrary dynamic import, unsafe deserialization, unsafe raw HTML, duplicate provider abstraction, or environment access outside Configuration. Schema `create_all` calls are confined to explicit registered Migration callbacks. Browser local/session storage appears only in the test asserting credentials are absent.
- `git diff --check`: passed.

Architecture review:

- Document 044 ownership and dependency direction are preserved across Core, infrastructure, domain Engines, extensions, Routing/API/Rendering, Admin, operations, Update, and Recovery.
- Provider-specific behavior remains behind Database, Storage, and Cache owners. Cross-Engine calls continue through registered public services.
- No migrations were required for the integration freeze.

Phase 12 gate: PASS. Phase 13 was not started. No distribution ZIP or release artifact was created.

## Phase 13 — Production Distribution Packaging

Status: Complete

Authoritative documents:

- `041-installation-bootstrap.md`
- `042-deployment-architecture.md`
- `043-production-operations.md`
- `044-system-integration-contracts.md`
- Phase 13 in `045-implementation-roadmap.md`

Implemented:

- Added externally invocable `favorite-cms migrate`, `favorite-cms install`, and `favorite-cms status` commands. The CLI coordinates existing Migration and Installation contracts, accepts caller-selected initial role and explicit authorization tuples, reads passwords through a hidden prompt or standard input, and emits only safe operator results.
- Added migration `platform.permission.001` for durable caller-selected role grants. Permission remains the authorization owner, and the installer creates no implicit administrator role, default grant, or authorization bypass.
- Added the neutral `favorite.theme.starter` resource package and Theme-owned discovery, validation, activation, and fallback integration. It supplies the existing polished starter presentation without executable Theme code or direct infrastructure access.
- Added the provider-neutral `mounted` Storage provider behind Storage Engine. It validates a durable operator-managed filesystem mount for production without selecting a cloud vendor. Durability, replication, and backup remain external operator responsibilities.
- Added a deterministic distribution manifest and build command. Staging is allowlisted, prohibited development/runtime-state artifacts and known test credentials are rejected, package metadata contains per-file checksums, ZIP timestamps are fixed, and repeated builds are byte-identical.
- Selected the frontend source-build distribution model: locked frontend source is shipped, dependencies are installed from the committed lockfile, a production Next.js build is created during deployment, and the Next.js production server remains required for Admin/frontend routes.
- Added provider-neutral production installation and runtime documentation, including PostgreSQL, mounted Storage, explicit migration/install commands, backend/frontend startup, ingress routing contracts, security requirements, limitations, and clean removal guidance.

Validation:

- Phase 13 focused Pytest: 4 passed.
- Full backend Pytest: 192 passed.
- Python compilation, frontend ESLint, TypeScript, and Next.js production build: passed.
- Playwright: 8/8 real browser assertions passed. The outer command retained the documented Windows development-server child process and timed out only after assertion completion.
- `git diff --check`: passed.
- A candidate archive was extracted into a clean temporary directory. Its Python package and declared runtime dependencies installed into an isolated virtual environment, and the generated `favorite-cms` console entrypoint executed successfully. Explicit migrations applied 10 ordered migrations; installation reached `installed`; repeated status reported zero pending migrations; backend readiness, public Routing → Rendering → starter Theme, and initial identity authentication passed.
- In the extracted candidate, `pnpm install --frozen-lockfile --offline`, `pnpm run build`, and the Next.js production server `/admin/login` smoke check passed. The package did not use the development database, E2E database, or existing Storage contents.
- Distribution validation found 124 approved files and no prohibited development artifacts, populated environment files, local databases, generated Storage, logs, bytecode, known test credentials, or private credentials. Repeated candidate builds produced the same SHA-256 digest.
- Live PostgreSQL installation and PostgreSQL backup/restore were not executed because no approved PostgreSQL server was available. PostgreSQL dependency/configuration and controlled provider boundaries are present. The mounted Storage contract was exercised using an isolated temporary mount; no vendor-specific durable Storage service was available for live validation.
- The formal Codex Security desktop scan service was unavailable in this tool surface. Local source and extracted-package audits reviewed command/code execution, dynamic loading, deserialization, environment ownership, schema ownership, filesystem ownership, browser credential storage, raw HTML, redirects, credential material, and duplicate registries; no new critical violation was found.

Architecture review:

- Installation remains coordination only. Migration owns schema evolution; Permission owns authorization; User and Authentication own identity and credentials; Theme owns Theme lifecycle/resources; Storage owns physical storage; Health owns readiness; and Core owns composition.
- Normal application startup still performs neither installation nor migration. Routing remains the sole Route registry; API remains the operation boundary; Rendering consumes resolved Route Context; Admin remains a Next.js API client.
- No marketplace, remote downloader, vendor deployment integration, automatic migration/install, arbitrary extension execution, universal administrator role, business feature, or Phase 14 work was introduced.

Phase 13 gate: PASS. Phase 14 was not started.

## Production Starter Theme

Status: Complete (post-roadmap Theme deliverable; no new platform phase)

Implemented:

- Upgraded the bundled package to `Favorite Starter` version `1.0.0` with a validated manifest and declared page template, shared layout, header/footer components, and stylesheet.
- Added Theme-owned, traversal-safe UTF-8 resource reading for declared resources only. Paths remain private to Theme Engine; resources are size-limited and package validation is repeated before access.
- Added generic public presentation operations for published Content listing, published Content detail, and Search results through the existing Routing and Rendering registries. Content and Search remain the data owners; the Theme receives escaped presentation models only.
- Added a responsive public homepage, accessible desktop/mobile navigation, hero and call-to-action, recent published Content cards, neutral empty states, listing/detail presentation, Search results/empty results, safe missing-resource responses, visible focus styles, skip navigation, and a semantic footer.
- Preserved Theme → Plugin → Platform fallback. The platform resources remain available when a Theme override is inactive, and failed Theme activation preserves the prior active Theme.
- Added Theme package documentation and real FastAPI/Next.js Playwright coverage for homepage, navigation, listing, detail, Search, empty Search, mobile menu, failed Theme activation, and safe missing resources.

Validation:

- Focused Theme/Rendering/Extension Pytest: 14 passed; the final required-resource regression was then included in the complete suite.
- Full backend Pytest: 197 passed.
- Python compilation, frontend ESLint, TypeScript, Next.js production build, and `git diff --check`: passed.
- Playwright: 8/8 real browser assertions passed. The outer command retained the known Windows development-server child process and timed out after assertion completion.
- Source audit found no Theme database, Storage, Authentication, Permission, Configuration/environment, dynamic import, command execution, deserialization, browser credential storage, or client-selected callable access. Content, titles, Search queries, summaries, and links are escaped or generated from fixed route prefixes before insertion. The Theme's small inline navigation/Search script selects only local DOM elements and navigates only to the fixed `/site/search/` prefix.

Known contract limits:

- No public Menu projection or public site-title Setting contract currently exists. The Theme therefore uses neutral, fixed platform navigation and identity rather than bypassing Menu/Settings authorization.
- Presentation request context does not expose query parameters. Search uses the documented Routing path parameter boundary (`/site/search/{query}`) instead of adding a second query parser to Rendering.
- Content pagination is not rendered because the current public adapter exposes only the bounded deterministic Content query result, not a public pagination metadata contract.

Architecture review:

- Routing remains the sole Route registry; Rendering remains composition owner; Theme owns package/resources; Content and Search own data; Admin remains an API client. The Theme does not import or access Database, Storage, Authentication, Permission, Configuration, Core internals, or filesystem APIs.
- No Core redesign, Plugin work, distribution ZIP rebuild, business feature, role, permission, provider, or new roadmap phase was introduced.

Theme implementation: PASS. Plugin development was not started.

## Phase 14 — First-Party Plugin Foundation

Status: Complete

Implemented:

- Added the bundled `favorite.plugin.example` version `1.0.0` data-only package with validated manifest, Core compatibility range, explicit capability declarations, and a strict versioned contribution document.
- Added the narrow declarative reference-runtime binding contract. Discovery remains manifest-only and performs no import or execution. Binding accepts only the fixed `reference-message` schema and cannot select a Python module, callable, service, path, or command from package input.
- Added explicit capability review to Plugin activation. Requested manifest capabilities must be supplied exactly for the reference package; they do not create role grants or bypass Permission Engine.
- Added durable Plugin-scoped message state through Settings Engine, a protected Plugin-owned GET/PATCH API operation, an owner-scoped Admin module, and a Plugin-owned public presentation through the existing Routing and Rendering contracts.
- Added deterministic deactivation cleanup across Routing, API, Rendering, Admin, and the active Setting definition. Stored Plugin state remains scoped and durable across an explicit restart/reactivation.
- Added failed candidate activation rollback that preserves the previous active runtime and removes candidate registrations.
- Added the validated reference package to the existing distribution allowlist. No new distribution ZIP was created.

Validation:

- Focused first-party Plugin Pytest: 4 passed.
- Full backend Pytest: 201 passed.
- Python compileall, frontend ESLint, TypeScript, Next.js production build, and `git diff --check`: passed.
- Playwright: 9/9 real browser assertions passed through Next.js and FastAPI. The new workflow covers capability denial before approval, activation, protected Plugin API state, Admin presentation, public Rendering, deactivation cleanup, state restoration, and the unchanged public homepage. The outer command retained the known Windows development-server child process and timed out after all assertions completed.
- Local source review found no dynamic import/execution, subprocess/system command, unsafe deserialization, environment access, direct Database/Storage Provider access, credential storage/exposure, unsafe raw HTML, unsafe redirect, or duplicate Routing/API registry in the new boundary. Plugin-controlled text is validated and HTML-escaped.
- The formal Codex Security scan could not be started because the desktop scan service tools were unavailable in this session. Its capability preflight passed in the documented parent-only degraded mode; the independent delegated baseline was unavailable by session policy.

Architecture review:

- Plugin Engine remains lifecycle owner; Routing remains the sole Route registry; API owns operations; Rendering owns presentation; Admin remains an authenticated API client; Permission remains authorization owner; Settings owns persisted application state; Database and Storage providers are not exposed to the Plugin.
- Core composition has no dependency on the optional reference Plugin. Theme and all existing CMS workflows remain operational.
- No marketplace, remote download, arbitrary executable loading, Plugin schema, implicit role/grant, business workflow, distribution rebuild, or Phase 15 work was introduced.

Phase 14 gate: PASS. Phase 15 was not started.

## Phase 15 — First-Party Plugin Suite

Status: Complete

Implemented:

- Added four independently discoverable, inactive-by-default, data-only packages: `favorite.plugin.seo`, `favorite.plugin.contact`, `favorite.plugin.sitemap`, and `favorite.plugin.analytics`, each version `1.0.0` with its own manifest, exact capability declarations, compatibility range, documentation, and fixed contribution schema.
- Extended the Phase 14 declarative binder to the fixed first-party suite kinds without accepting package-selected modules, callables, services, scripts, commands, or paths.
- Added owner-scoped Rendering decorators and an explicit XML presentation content type. Routing remains the sole Route registry; decorators are deterministic, removable, and failure-isolated.
- SEO provides protected Admin/API configuration and safe site-level title, description, canonical, robots, and Open Graph contributions. Per-content SEO editing remains unavailable because SEO Engine reserves resource contributions for the registered Content owner.
- Contact Form provides protected configuration, a public validated form, honeypot handling, bounded Plugin-scoped pending submissions, safe errors, and no arbitrary redirect/raw HTML. Actual external delivery remains unavailable because no approved durable Notification provider configuration contract exists.
- Sitemap provides protected public-origin configuration and deterministic XML containing only published Content visible through the Content public contract.
- Analytics provides protected `none`/`first-party` configuration and a fixed safe presentation metadata contribution. It accepts no script URL, secret, external request, or commercial provider.
- Admin remains a Next.js API client; every management API independently requires Authentication and `admin.extensions.manage`. No role or grant is created implicitly.
- Added all packages to the existing distribution allowlist. They ship inactive; no distribution ZIP was created.

Validation:

- Phase 15 focused backend validation: 5 passed; broader Plugin/Rendering/distribution validation: 16 passed.
- Full backend Pytest: 206 passed with one existing Starlette deprecation warning.
- Python compileall, frontend ESLint, TypeScript, Next.js production build, and `git diff --check`: passed.
- Playwright: 10/10 real browser workflows passed through Next.js and FastAPI. Coverage includes capability approval, activation/deactivation, Admin authorization, SEO configuration/rendering, Contact validation/submission, Sitemap XML, Analytics disabled/enabled states, cleanup, failure isolation, and existing Theme/Content/Media/Search/Localization regressions. The outer command retained the documented Windows development-server process and timed out only after all ten tests reported `ok`.
- Distribution staging validation included all five bundled first-party Plugins and excluded tests, databases, caches, secrets, `node_modules`, local Storage, and Playwright artifacts.
- Local source audit found no eval/exec, subprocess/system execution, dynamic import, unsafe deserialization, arbitrary filesystem/environment/Database/Storage Provider access, secret exposure, unsafe redirect, raw HTML injection, browser credential storage, SSRF-capable URL fetch, user-selected script/callable/service, hidden Permission grant, or duplicate infrastructure in the new suite.
- Formal Codex Security scan tooling was unavailable in this desktop session. The scan preflight reached ready with the documented parent-only degraded path; no formal scanner result is claimed.

Architecture review:

- Core composition is unchanged. Plugin Engine owns lifecycle; Routing owns matching; API owns operations; Rendering owns presentation; Settings owns persisted Plugin state; Content owns published resources; Authentication and Permission remain separate; Notification remains delivery owner; Database and Storage internals are not exposed.
- No marketplace, remote download, SMTP provider, analytics vendor, arbitrary executable loading, Plugin schema, implicit administrator/grant, final distribution ZIP, or Phase 16 work was introduced.

Phase 15 gate: PASS. Phase 16 was not started.

## Phase 16 — CMS Usability, Release Hardening, and First-Run Experience

Status: Complete

Implemented:

- Added a permission-filtered Admin dashboard using public Content, Media, Theme/Plugin, and Health contracts. It presents safe summaries, active Theme state, readiness, and authorized quick actions without private Database queries or topology exposure.
- Expanded the generic Content management UI with draft creation, deterministic listing, lifecycle state badges, editing, publishing, validation feedback, confirmed deletion, empty states, and safe failures through the existing Content Engine.
- Added a deterministic permission-filtered Media listing contract within Media Engine and exposed upload/list metadata through Admin without exposing Storage references or physical paths.
- Improved Settings, Theme/Plugin lifecycle, capability approval, diagnostics, responsive layout, keyboard focus, loading, empty, success, error, and degraded-state presentation. Existing Search, Localization, public Theme navigation, content listing/detail, mobile navigation, and missing-resource behavior remain intact.
- Documented the five current Admin permission tuples as an explicit first-run operator choice. No administrator role, implicit grant, or automatic installation behavior was added.

Validation:

- Phase 16 focused backend tests cover permission-filtered dashboard data, Content edit/publish/delete, Media listing, deterministic ordering, and visibility filtering.
- Full backend Pytest: 209 passed with one existing Starlette deprecation warning.
- Python compileall, frontend ESLint, TypeScript, and Next.js production build: passed.
- Playwright: 10/10 real browser tests passed through Next.js and FastAPI, including the enhanced dashboard, Content create/edit/publish/list, Media upload/list, Settings, Theme/Plugin lifecycle failures, Health diagnostics, Search, Localization, public Content, missing resources, mobile navigation, Authentication/Permission, and safe session behavior. The outer command retained the known Windows development-server child process until timeout after all assertions completed.
- Distribution manifest staging remained valid and includes the modified runtime files while continuing to exclude tests, caches, databases, generated Storage, secrets, logs, `node_modules`, and Playwright artifacts. No distribution ZIP was created.
- Formal Codex Security scan startup was unavailable because the desktop scan service tools were not exposed. Local source and diff audits reviewed dynamic execution/import, process execution, deserialization, environment ownership, schema ownership, filesystem ownership, browser credential storage, raw HTML, redirects, secret exposure, authorization, and duplicate registries; no new critical violation was found.

Architecture review:

- Core composition, Routing, API, Rendering, Admin, Content, Media, Storage, Theme, Plugin, Settings, Authentication, Permission, and Health ownership remain unchanged. Admin continues to be a Next.js API client and every protected operation independently enforces backend Permission.
- No direct Database/Storage Provider access was added to Admin, no schema or migration was required, and no Phase 17, marketplace, remote update, deployment vendor, SaaS, or business-specific functionality was introduced.

Known limits:

- Content types and editable fields remain those registered by owning Content extensions; Admin does not invent a schema or rich editor.
- Media upload remains the bounded generic text/document surface already supported by the production API; binary browser upload and media transformation UX require a separately documented public upload contract.
- Dashboard summaries are bounded to the existing public query contracts; unavailable summaries display an unknown state rather than using private Database counts.

Phase 16 gate: PASS. Phase 17 was not started.

## Phase 17 — Production Release Candidate, Final Distribution, and Clean-Install Gate

Status: Complete

Release: `favorite-cms` version `0.1.0`

Implemented and corrected:

- Finalized the deterministic source-build distribution and added a hard version-consistency gate across Python metadata, frontend metadata, distribution manifest, archive filename, and package metadata.
- Fixed a release-blocking clean-bootstrap defect: the production platform now registers its generic Page Content Type, Media access contract, site-title Setting, searchable Content contract, and base Localization resources through their owning Engines. Admin coordination indexes Content mutations through Search; no private Database or Storage access was added.
- Preserved fail-closed authorization by defining explicit domain permissions separately from Admin module permissions. Installation still requires the caller to select and grant every permission; no administrator role or implicit grant exists.
- Isolated each Playwright run with a unique SQLite database and Storage root so browser validation never reuses repository test state.
- Hardened package exclusion checks for IDE/OS metadata and coverage artifacts, and finalized README, distribution, deployment, and operations instructions for the actual migration, installation, build, runtime, Health, authorization, Storage, and PostgreSQL boundaries.
- Replaced the earlier `0.1.0` candidate artifact using the official deterministic builder after all release gates passed. No additional ambiguous ZIP was created.

Validation:

- Phase 17 focused backend tests: 3 passed; Phase 13–17 packaging/installation/usability group: 9 passed.
- Full backend Pytest: 212 passed with one existing Starlette deprecation warning.
- Python compileall, frontend ESLint, TypeScript, Next.js production build, and `git diff --check`: passed.
- Playwright: 10/10 real browser workflows passed without HTTP interception. The outer Windows command timed out only after all assertions reported `ok`, because the known development-server child process remained alive.
- Two independent deterministic candidates contained identical bytes and SHA-256: `4389c7e6390c0758f8d3437dcc341bcfaedbb8bf93522e2b0eb1137762b13dd5`.
- Final archive: `dist/favorite-cms-0.1.0.zip`, 204,029 bytes, 143 approved files. The independently calculated digest matches `dist/favorite-cms-0.1.0.sha256`.
- Actual ZIP inspection found all required backend/frontend runtime files, Starter Theme, and five approved first-party Plugins. It found no tests, `.git`, `.github`, `.venv`, `node_modules`, `.next`, caches, bytecode, databases, generated Storage, populated environment files, logs, Playwright artifacts, known test credentials, or private-key markers.
- The final ZIP was extracted into a clean directory. A fresh virtual environment installed the packaged Python project and dependencies; `pip check` passed. Explicit migration applied 10 migrations; installation progressed from uninstalled to installed; status reported zero pending migrations; the initial identity authenticated; repeated installation/status behavior remained covered by regression tests.
- In the extracted package, `pnpm install --frozen-lockfile`, Next.js production build, and production server startup passed. Production dependencies resolved to Next.js, React, and React DOM; the lockfile passed pnpm's supply-chain policy check.
- Extracted-package FastAPI and Next.js processes started independently. Liveness, public Routing/Rendering/Starter Theme, Admin login/dashboard, five permission-filtered modules, Search, and Localization passed. Seven additional clean-candidate Playwright assertions passed for login, dashboard, permission navigation, HttpOnly/SameSite cookie, empty browser credential storage, public Theme rendering, and navigation.
- Source and archive audits found no new arbitrary execution/import, unsafe deserialization, unsafe redirects/raw HTML, secret exposure, frontend Database/Storage access, implicit grant, or duplicate Routing/API/Auth/Permission infrastructure. Formal Codex Security scanner: NOT EXECUTED because the desktop scan service was unavailable.

External limitations:

- Live PostgreSQL installation and provider-specific PostgreSQL backup/restore were not executed because no approved PostgreSQL server was available. PostgreSQL configuration/dependency contracts and controlled failure paths remain validated.
- The mounted Storage provider was exercised against a new isolated filesystem mount. No external durable Storage service, reverse proxy, TLS terminator, or process supervisor was available or selected; these remain operator-owned production dependencies.

Architecture review:

- Core, Routing, API, Rendering, Admin, Database, Migration, Storage, Content, Media, Settings, Theme, Plugin, Authentication, Permission, Health, Update, Recovery, Scheduler, and Queue ownership remains unchanged. Startup still performs neither migration nor installation.
- No marketplace, remote download/update service, cloud provisioning, SaaS, multi-tenancy, business feature, vendor deployment integration, duplicate infrastructure, or Phase 18 work was introduced.

Phase 17 gate: PASS. Phase 18 was not started.

## Phase 18 — Production Distribution Hardening and Release Validation

Status: Complete

Release: `favorite-cms` version `0.1.0`

Hardening completed:

- Strengthened distribution validation to reject private-key material and populated production database/signing-secret values in environment templates, while preserving deterministic ordering, fixed archive metadata, and required runtime inclusion.
- Added focused operator CLI tests for command help, deterministic success/failure exit behavior, uninstalled status, safe failure output, and credential/configuration redaction.
- Removed the legacy public frontend environment fallback for the backend URL. Next.js transport now consumes only the server-side `FAVORITE_API_URL` contract (with the documented local default); no backend credential or endpoint configuration is sourced from `NEXT_PUBLIC_*`.
- Added a reusable clean-candidate browser smoke covering the installed identity, permission-filtered Admin, session safety, Content, Media, Settings, Health, Plugin lifecycle, active Theme, Search, Localization, public Routing/Rendering, missing resources, mobile navigation, and logout through real transport without interception.
- Clarified operator CLI exit handling, Update scope, and Recovery/provider limitations in the distribution and operations documentation.

Validation:

- Focused Phase 18 tests: 6 passed. Focused release, Update, Recovery, Installation, Configuration, Database, Migration, and Storage validation: 52 passed.
- Full backend Pytest: 218 passed with one existing Starlette TestClient deprecation warning.
- Python compileall, frontend ESLint, TypeScript, Next.js production build, and `git diff --check`: passed.
- Repository Playwright: 10/10 real browser tests passed. The outer Windows command timed out only after every assertion reported success because the known development-server child process remained alive.
- Two independently staged final archives were byte-identical with SHA-256 `1d0fcb5322c67691cf5d12eb1ecb539085f7495aeb3881fc38d05e7fdf4d4934`.
- The final package contains 143 approved files and no prohibited tests, caches, bytecode, local databases, generated Storage, populated environment files, private keys, known test credentials, `node_modules`, `.next`, or Playwright artifacts.
- The rebuilt final ZIP was extracted outside the repository. A fresh Python environment installed the packaged dependencies and passed `pip check`; CLI status reported uninstalled; explicit migration applied 10 migrations; installation reported installed and zero pending migrations. Frozen frontend dependency installation and production build passed.
- The extracted candidate's FastAPI and Next.js production servers passed 21/21 additional real browser assertions with no HTTP interception. Candidate processes were stopped after validation.
- Update validation covered checksum/compatibility checks, target locking, migration coordination, repeated-update rejection, Plugin state/version transition, Theme rollback, and activation failure isolation using the existing simulated extension-package contract; no fictional `0.2.0` platform release was created.
- Recovery validation covered verified Backup Sets, checksum/tamper rejection, platform/provider compatibility, database and mounted Storage restoration, Extension state restoration, rollback protection, and restart discovery for the supported SQLite/mounted test boundary.
- Source and final-package audits reviewed dynamic execution/import, process execution, deserialization, filesystem traversal, redirects, raw HTML/script boundaries, browser credential storage, secrets, private keys, implicit grants, and duplicate infrastructure. No new critical violation was found. Formal security scanner: NOT EXECUTED because the desktop scan service was unavailable.

External limitations:

- Live PostgreSQL connectivity and PostgreSQL-native backup/restore were NOT EXECUTED because no approved PostgreSQL server was available. Configuration/provider selection and controlled failure behavior remain tested.
- Mounted Storage was validated against fresh isolated operator-owned directories. No external durable Storage service was selected or live-tested; reverse proxy, TLS termination, process supervision, and provider backup policy remain operator responsibilities.

Architecture review:

- Core, Routing, API, Rendering, Admin, Authentication, Permission, Content, Media, Storage, Settings, Plugin, Theme, Migration, Update, Recovery, Queue, Scheduler, and Health ownership remain unchanged. Startup still performs neither migration nor installation.
- No marketplace, remote Plugin execution/download, implicit administrator, duplicate registry, new business feature, or Phase 19 functionality was introduced.

Phase 18 gate: PASS. Phase 19 was not started.

## Phase 19 — Real-World Release Candidate and First-Install Validation

Status: Complete

Release: `favorite-cms` version `0.1.0`

Operator-experience validation:

- Repeated the documented zero-to-website workflow from a deterministic ZIP in an empty directory outside the repository. A fresh Python environment installed cleanly, CLI help was discoverable, initial status was uninstalled, 10 explicit migrations applied, caller-selected role and authorization tuples installed the first identity, status became installed with zero pending migrations, and repeated installation remained idempotent.
- Expanded the clean-candidate browser smoke to cover draft visibility and public isolation, draft editing, publishing, public listing/detail, Search, published editing, confirmed deletion, public disappearance, and controlled missing-resource behavior.
- Validated the supported bounded text/document Media workflow, metadata/listing, distinct Media identity for repeated names, Settings update, safe diagnostics, all five bundled first-party Plugins, explicit capability approval, deactivation cleanup, Plugin state restoration, Starter Theme discovery/rendering, Localization fallback, desktop/tablet/mobile presentation, secure session behavior, and logout invalidation.
- Audited documentation as a new operator. README and distribution/runbook guidance now state the Admin/public URLs, first-operator walkthrough, explicit permission meaning, inactive-by-default Plugin behavior, supported Media surface, Theme-package boundary, and unsupported capabilities without inventing hidden roles or product features.

Validation:

- Full backend Pytest: 218 passed with one existing Starlette TestClient deprecation warning.
- Python compileall, frontend ESLint, TypeScript, Next.js production build, and `git diff --check`: passed.
- Repository Playwright: 10/10 real browser tests passed. The outer Windows command timed out only after every assertion completed because the known development-server child process remained alive.
- Clean extracted candidate: 30/30 real browser assertions passed without interception, including editing already-published Content and verifying the updated public output. Accessible navigation passed at tablet 768×1024 and mobile behavior passed at 390×844.
- Two independent source-build archives were byte-identical. The resulting package contains 143 approved files, no prohibited development/runtime state, and no known credential/private-key markers.
- Local source/package security review covered Auth/Permission, protected API access, cookie and browser storage safety, redirects, missing/malformed resources, Media traversal at the owning Storage contract tests, raw HTML boundaries, secrets, hidden grants, and duplicate infrastructure. Formal security scanner: NOT EXECUTED because the desktop scan service was unavailable.

Documented product boundaries:

- Browser Media in `0.1.0` supports bounded UTF-8 text/document resources and safe metadata/listing. Binary image upload, transformation, and browser deletion require a future documented Media contract.
- The distribution contains one valid production Starter Theme. Invalid Theme rejection, fallback, and previous-theme preservation are validated through Theme Engine tests rather than exposing a deliberately broken operator package.
- Installation authorization tuples remain deliberately explicit. A friendlier permission-preset UX would require a future documented contract; no universal administrator or implicit grant was introduced.

External limitations remain unchanged: live PostgreSQL and PostgreSQL-native restore were not executed; no external durable Storage service, reverse proxy, TLS terminator, or process supervisor was selected or validated.

Architecture review: PASS. Existing Core, Routing, API, Rendering, Admin, Authentication, Permission, domain Engine, Plugin, Theme, Migration, Update, Recovery, Queue, Scheduler, and Health ownership remains unchanged. Phase 20 was not started.

Phase 19 gate: PASS.

## Phase 20 — Final Production Readiness and Release Hardening

Status: Complete

Release: `favorite-cms` version `0.1.0`

Hardening completed:

- Strengthened the official distribution builder so the manifest version must match all runtime version consumers, unsafe absolute/traversal manifest entries fail closed, and source or staged symlinks are rejected before archive assembly.
- Added deterministic Phase 20 regression tests for runtime version consistency, conflicting runtime metadata, and source-symlink rejection.
- Clarified in the distributable operator documentation that repository-controlled security audits do not constitute a formal external security-scanner result.
- Preserved explicit installation authorization, explicit migration, inactive-by-default Plugins, server-only frontend backend resolution, and all established Engine ownership boundaries.

Validation:

- Focused Phase 20/release tests: 12 passed. Full backend Pytest: 221 passed with one existing Starlette TestClient deprecation warning. Python compileall passed.
- Frontend ESLint, TypeScript, and Next.js production build passed.
- Repository Playwright: 10/10 real browser assertions passed without interception. The outer Windows command timed out after all assertions because the known development-server child process remained alive.
- Two independently staged final archives were byte-identical with SHA-256 `74469f7dd6a439e3b3c78f52fc37c8e7bf34bcf1d92d2e543297f7208a1632f2`.
- Final archive: `dist/favorite-cms-0.1.0.zip`, 205,788 bytes, 143 approved files. `dist/favorite-cms-0.1.0.sha256` independently matched; archive extraction and integrity checks passed; prohibited entries numbered zero.
- The final rebuilt ZIP was extracted outside the repository. A fresh virtual environment installed the packaged project, `pip check` passed, CLI help worked, status began uninstalled, 10 explicit migrations applied, installation became installed with zero pending migrations, and repeated installation remained idempotent.
- The final extracted frontend passed `pnpm install --frozen-lockfile`, lockfile supply-chain policy validation, and a production Next.js build. Candidate FastAPI and Next.js production processes started independently and stopped after validation.
- Final clean-candidate browser smoke: 30/30 real assertions passed without interception across Authentication/session safety, permission-filtered Admin, Content lifecycle, Media, Settings, five bundled Plugins, Starter Theme, Search, Localization, backend Routing/Rendering, safe missing resources, responsive navigation, and logout.
- Source and final-package audits checked dynamic/process execution, arbitrary imports/callables, deserialization, filesystem and symlink traversal, raw HTML/redirect boundaries, browser credential storage, secrets/private keys, implicit grants, external requests, and duplicate infrastructure. No critical regression was found. FORMAL SECURITY SCANNER: NOT EXECUTED because the desktop scan service was unavailable.
- `git diff --check` passed after the final documentation update.

External limitations:

- Live PostgreSQL and PostgreSQL-native backup/restore were NOT EXECUTED because no approved server was available. Configuration selection and fail-closed provider behavior remain covered by repository tests.
- Mounted Storage was validated only against fresh isolated operator-owned directories. No external durable Storage service, reverse proxy, TLS terminator, or process supervisor was selected or validated.

Architecture review: PASS. Core, Routing, API, Rendering, Admin, Authentication, Permission, Content, Media, Storage, Settings, Plugin, Theme, Migration, Update, Recovery, Scheduler, Queue, and Health ownership remains unchanged. Startup still performs neither migration nor installation. No marketplace, remote execution/download, hidden grant, universal administrator, business feature, duplicate infrastructure, or Phase 21 work was introduced.

Phase 20 gate: PASS. Phase 21 was not started.

## Phase 21 — Release Candidate and Operator-Readiness Validation

Status: Complete

Release candidate: `favorite-cms` version `0.1.0`

Validation completed:

- Recorded the existing release baseline before validation: `dist/favorite-cms-0.1.0.zip`, 205,788 bytes, SHA-256 `74469f7dd6a439e3b3c78f52fc37c8e7bf34bcf1d92d2e543297f7208a1632f2`; the checksum file matched.
- Audited README, distribution documentation, deployment and operations runbooks from an operator-only perspective. They cover package contents/exclusions, prerequisites, production configuration, explicit migration/installation/status, caller-selected authorization tuples, runtime topology, Admin/public URLs, Plugin/Theme operation, Media scope, Update/Recovery limits, PostgreSQL/Storage limits, proxy/TLS/supervision ownership, and formal-scanner limitations. No distributable documentation correction was required.
- Extracted the preserved ZIP into a clean directory outside the repository. A fresh Python virtual environment installed the packaged project, `pip check` passed, CLI help worked, status began uninstalled, 10 migrations applied, repeated migration applied zero, explicit installation completed, and status reported installed with zero pending migrations.
- The clean extracted frontend passed frozen lockfile installation, the 401-entry supply-chain policy check, and the Next.js production build. Independent FastAPI and Next.js production processes started and were stopped after validation.
- Clean-candidate browser journey: 30/30 real assertions passed without interception, covering Authentication/session safety, permission-filtered Admin, Content draft/edit/public isolation/publish/search/detail/update/delete, Media, Settings, five bundled Plugins, Starter Theme, Localization, backend Routing/Rendering markers, controlled missing resources, tablet/mobile navigation, and logout invalidation.
- Full backend Pytest: 221 passed with one existing Starlette TestClient deprecation warning. Focused release/Installation/Migration/Update/Recovery/Distribution group: 33 passed. Python compileall, ESLint, TypeScript, Next.js production build, and `git diff --check` passed.
- Repository Playwright: 10/10 real assertions passed without interception. The outer command timed out only during the known Windows development-server child-process teardown.
- Two temporary distribution rebuilds and the preserved release artifact were byte-identical: 143 entries and identical SHA-256 `74469f7dd6a439e3b3c78f52fc37c8e7bf34bcf1d92d2e543297f7208a1632f2`. No absolute or traversal paths were present.
- Source and staged-package audits found zero prohibited files, known credential/private-key markers, frontend secret configuration, dynamic execution/import, unsafe deserialization, or Plugin/Theme private-infrastructure access. Environment access remains owned by Configuration. FORMAL SECURITY SCANNER: NOT EXECUTED because the desktop scanner was unavailable.

Artifact policy:

- No release-blocking defect or distributable documentation change was found. The existing final ZIP and checksum were preserved rather than replaced. Temporary Phase 21 rebuilds were validation-only.

External limitations remain unchanged: live PostgreSQL and PostgreSQL-native backup/restore were NOT EXECUTED; no external durable Storage provider, reverse proxy, TLS terminator, process supervisor, or formal security scanner was available.

Architecture review: PASS. No ownership change, duplicate infrastructure, automatic migration/installation, hidden grant, universal administrator, remote package execution, marketplace, business feature, or Phase 22 work was introduced.

Phase 21 gate: PASS. Phase 22 was not started.

## Phase 22 — Extension and Developer Contract Hardening

Status: Complete

Release: `favorite-cms` version `0.1.0`

Implemented:

- Added a Content-owned optional SEO metadata and published-only projection boundary. The first-party SEO Plugin now reads and updates that boundary through authenticated, permission-checked Content operations and emits escaped canonical, robots, description, and Open Graph metadata only for public Content.
- Added a provider-neutral Notification delivery contract for Contact. Notification owns recipient/channel validation, pending/delivered/failed state, attempts, normalized failures, and a bounded durable delivery ledger persisted through Settings and restored after restart. No email adapter, SMTP, webhook, provider secret, arbitrary endpoint, or live external-delivery claim was introduced.
- Improved Plugin/Theme Admin presentation with required and granted capabilities, compatibility, lifecycle state, and safe activation-failure details. Backend authorization remains authoritative and capability approval remains explicit.
- Added developer documentation for declarative Theme and first-party Plugin packages, lifecycle cleanup/rollback, scoped state, safe public contributions, testing, packaging, and prohibited private infrastructure access.
- Browser binary Media and image transformation remain intentionally unavailable: the current architecture has no approved signature-sniffing, sanitization, or image-processing boundary. Existing bounded UTF-8 text/document Media remains unchanged.
- Friendly permission presets remain future work because no safe preset-expansion contract exists. Installation continues to require transparent explicit authorization tuples.

Validation:

- Focused Phase 22/Notification/Plugin tests: 16 passed. Full backend Pytest: 226 passed with one existing Starlette TestClient deprecation warning.
- Python compileall, frontend ESLint, TypeScript, Next.js production build, and `git diff --check` passed.
- Repository Playwright: 10/10 real assertions passed without HTTP interception, including Content-owned SEO management and escaped backend-rendered metadata. The outer Windows command timed out only during the known development-server child-process teardown.
- Two independently staged archives were byte-identical with 144 approved entries and zero prohibited entries. Clean extraction, fresh Python environment installation, `pip check`, explicit 10-migration installation, zero pending migrations, frozen frontend dependency installation, and production frontend build passed.
- Clean-candidate browser smoke: 30/30 real assertions passed without interception across Authentication/session safety, permission-filtered Admin, Content, Media, Settings, all bundled Plugins, Starter Theme, Search, Localization, backend Routing/Rendering, missing resources, responsive navigation, and logout.
- Source/package review checked code/process execution, imports/callables, deserialization, path/symlink traversal, raw HTML and redirects, SSRF/external URLs, browser credential storage, secrets/private keys, owner boundaries, hidden grants, and duplicate infrastructure. No critical regression was found. FORMAL SECURITY SCANNER: NOT EXECUTED because the desktop scan capability was unavailable.

External limitations remain unchanged: no live PostgreSQL server, PostgreSQL-native backup/restore, approved external email provider, external durable Storage provider, reverse proxy, TLS terminator, or process supervisor was available or claimed as validated.

Architecture review: PASS. Content owns Content/SEO metadata, Notification owns delivery, Settings owns persisted application state, Plugins use scoped public facades, and all existing Core/Route/API/Rendering/Auth/Permission/Media/Storage/Theme/Plugin boundaries remain intact.

Phase 22 gate: PASS. Phase 23 was not started.

## Phase 23 — Authoring and Extension Operations Usability

Status: Complete

Release: `favorite-cms` version `0.1.0`

Implemented:

- Improved generic Content authoring with explicit draft/public guidance, bounded field help, safe plain-text preview, clearer save/publish feedback, and accessible lifecycle actions. Corrected Content edits to preserve Content-owned SEO metadata instead of replacing metadata with an empty object.
- Exposed optional Content-owned SEO fields in Admin through the existing authenticated Content/SEO Plugin API: SEO title, meta description, canonical path with origin-aware preview, robots, Open Graph title/description/image, safe defaults, and draft privacy guidance. Empty SEO titles retain the Content-title fallback, and existing metadata records remain compatible.
- Added a Notification-owned aggregate delivery summary for the Contact Plugin. Admin displays only pending/delivered/failed/attempt counts and provider availability; recipients, payloads, credentials, adapters, and provider internals remain hidden. The no-provider state is reported honestly.
- Clarified the supported Media form as bounded UTF-8 plain text, surfaced filename/type/MIME/size limits, documented distinct identities for duplicate names, and retained Media-to-Storage ownership with no physical path exposure. Binary Media remains deferred.
- Expanded declarative Theme/Plugin developer documentation with minimal package examples, manifest/contribution structure, lifecycle cleanup and rollback, scoped state, testing, distribution, and prohibited behaviors.
- Improved Admin section navigation, semantic status feedback, focus visibility, validation help, counters, empty states, extension capability/compatibility diagnostics, and mobile presentation without adding a second client data or routing layer.
- Authorization presets remain deferred because there is no Core-owned transparent preset-expansion contract. Explicit authorization tuples and fail-closed permission checks remain unchanged.

Validation:

- Focused Phase 23 tests: 3 passed. Combined Phase 22/23 Notification/Plugin suite: 19 passed. Full backend Pytest: 229 passed with one existing Starlette TestClient deprecation warning.
- Python compileall, frontend ESLint, TypeScript, Next.js production build, and `git diff --check` passed.
- Repository Playwright: 10/10 real assertions passed without HTTP interception. The outer Windows command timed out only during the known development-server child-process teardown.
- Two independently staged archives were byte-identical with SHA-256 `261874d53d294a52db8451454d5319471ed74750fc1a1dc383bf3d47cfcc60f3`, 144 approved entries, and zero prohibited entries.
- The candidate was extracted outside the repository. A fresh Python environment installed the package, `pip check` passed, 10 explicit migrations applied, installation completed with zero pending migrations, frozen frontend dependencies installed, and the production frontend build passed.
- Clean-candidate browser smoke: 30/30 real assertions passed without interception across Authentication/session safety, permission-filtered Admin, Content lifecycle, Media, Settings, all bundled Plugins, Starter Theme, Search, Localization, backend Routing/Rendering, missing resources, responsive navigation, and logout.
- Parent-led source/package security review checked dynamic/process execution, arbitrary imports/callables, deserialization, path/symlink traversal, raw HTML and redirects, SSRF/external URLs, browser credential storage, secrets/private keys, owner boundaries, hidden grants, and duplicate infrastructure. No critical regression was found. FORMAL SECURITY SCANNER: NOT EXECUTED because the desktop scanner capability was unavailable; independent scan delegation was unavailable under the active runtime policy.

External limitations remain unchanged: no live PostgreSQL server, PostgreSQL-native backup/restore, approved external Notification/email provider, external durable Storage provider, reverse proxy, TLS terminator, or process supervisor was available or claimed as validated. Binary Media and authorization presets remain explicitly deferred contracts.

Architecture review: PASS. Content owns authoring and SEO metadata; Notification owns delivery state; Media delegates bytes to Storage; Admin remains an authenticated API client; Plugin and Theme lifecycle ownership and all Core/Route/API/Rendering/Auth/Permission boundaries remain unchanged.

Phase 23 gate: PASS. Phase 24 was not started.

## Phase 24 — Operational Maturity, Observability, and Maintainability

Status: Complete

Release: `favorite-cms` version `0.1.0`

Implemented:

- Added an authorized operator diagnostics snapshot owned by Health and composed from safe public owner contracts. Public liveness/readiness responses remain minimal.
- Added redacted configuration-presence reporting, provider types, explicit migration/installation state, platform version, Theme, Queue/Scheduler, Notification, Update, Recovery, Content SEO, and supported Media mode.
- Added safe owner status contracts for Configuration, Notification, Installation, Update, and Recovery. These expose states and counts only, never values, paths, payloads, credentials, package internals, or service objects.
- Improved the permission-filtered dashboard and Diagnostics UI with semantic status cards, dependency messages, explicit lifecycle guidance, responsive layouts, and accessible operational headings.
- Reused existing API request IDs, error IDs, and stable error categories. No duplicate logging, tracing, Health, Routing, or API infrastructure was introduced.
- Documented diagnostic meanings, explicit startup behavior, Update/Recovery boundaries, and unchanged provider/operator responsibilities.

Validation:

- Focused Phase 24: 4 passed. Full backend Pytest: 233 passed with one existing Starlette TestClient deprecation warning.
- Python compileall, ESLint, TypeScript, Next.js production build, and `git diff --check` passed.
- Repository Playwright: 10/10 real assertions passed without interception. The outer Windows command timed out only during the known development-server child-process teardown.
- Two final distribution builds were byte-identical with SHA-256 `1315317fbafc08028fcadb146c0374ef826afaa6d1762b01ab52f69dea561281`, 144 approved entries, and zero prohibited or credential-marker entries.
- Final ZIP clean extraction, packaged backend installation, explicit 10-migration installation, zero pending migrations, frozen frontend installation, and production frontend build passed.
- Clean-candidate browser smoke: 30/30 real assertions passed without interception.
- Parent-led source/package security audit found no critical regression. FORMAL SECURITY SCANNER: NOT EXECUTED because the desktop scanner capability was unavailable; independent scan delegation was unavailable under the active runtime policy.

External limitations remain unchanged: live PostgreSQL, PostgreSQL-native backup/restore, external durable Storage, external Notification delivery, reverse proxy, TLS, and process supervision were not available or remain operator/provider-owned.

Architecture review: PASS. Health composes diagnostics through owner contracts; Admin remains a permission-filtered API client; all established ownership boundaries remain unchanged. No automatic migration, automatic installation, remote update, telemetry, duplicate infrastructure, or Phase 25 work was introduced.

Phase 24 gate: PASS. Phase 25 was not started.

## Phase 25 — Final Production Readiness and Release Closure

Status: Complete

Release: `favorite-cms` version `0.1.0`

Release-closure result:

- Audited the repository-owned runtime, authorization boundaries, lifecycle contracts, operator documentation, deterministic builder, and current release artifact.
- Corrected one installer idempotency defect: a repeated `favorite-cms install` invocation could persist newly supplied role grants before the Installation Engine returned its existing installed state. The CLI now returns the persisted installed result before Theme or Permission mutation, so a repeated installation cannot silently widen authorization.
- Added a focused regression proving that repeated installation with a different authorization tuple does not add that grant.
- Preserved explicit migration and installation, caller-selected authorization tuples, fail-closed Permission enforcement, inactive-by-default Plugins, and all existing ownership boundaries.

Validation:

- Focused Phase 25: 1 passed; focused installer/release group: 11 passed. Full backend Pytest: 234 passed with one existing Starlette TestClient deprecation warning.
- Python compileall, ESLint, TypeScript, Next.js production build, and `git diff --check`: passed.
- Repository Playwright: 10/10 real browser assertions passed without interception. The outer Windows process timed out only during the known development-server child-process teardown.
- Two independent distribution builds were byte-identical with 144 approved entries and zero prohibited entries.
- Final ZIP clean extraction, fresh Python installation, `pip check`, CLI help/status, explicit 10-migration installation, zero pending migrations, repeated migration, explicit installation, idempotent repeated installation, frozen frontend installation, production frontend build/startup, and backend production startup passed.
- Clean-candidate browser smoke: 30/30 real assertions passed without interception.
- Parent-led source and package security review found no critical regression. FORMAL SECURITY SCANNER: NOT EXECUTED because the desktop scan service was unavailable; independent scan delegation was unavailable under the active runtime policy.

External limitations remain unchanged: live PostgreSQL, PostgreSQL-native backup/restore, external durable Storage, external Notification delivery, reverse proxy, TLS, and process supervision were not executed or remain operator/provider-owned. Binary Media and authorization presets remain intentionally deferred.

Architecture review: PASS. No duplicate infrastructure, owner bypass, automatic migration/installation, hidden grant, universal administrator, marketplace, remote execution, or Phase 26 functionality was introduced.

Phase 25 gate: PASS. Phase 26 was not started.

## Phase 26 — Final Release Closure and Operator Handoff

Status: Complete

Release: `favorite-cms` version `0.1.0`

Closure result:

- Completed the final repository-controlled architecture, version, operator-documentation, configuration, authorization, lifecycle, security, dependency, distribution, and clean-install review without finding a release defect.
- Preserved the Phase 25 artifact because no shipped runtime or operator-documentation change was required. This implementation-status entry is not part of the distribution allowlist.
- Verified two fresh distribution builds are byte-identical to the authoritative artifact: SHA-256 `4c92d8a7539432a0ebb92c303ff4f482117c9202e16410495f3e0662753d7380`, 218,507 bytes, 144 approved entries, zero prohibited entries, zero unsafe paths, zero duplicate entries, and no credential/private-key markers.
- Validated clean extraction outside the repository, a fresh Python environment and packaged install, `pip check`, CLI help/status, 10 explicit migrations, zero pending migrations, explicit caller-selected installation authorization, zero-op repeated migration, idempotent repeated installation, frozen frontend installation, production build/startup, and backend production startup.
- Clean-candidate browser smoke completed 30/30 real assertions without interception. Repository Playwright completed 10/10 real assertions; its outer process timed out only during the known Windows child-process teardown.
- Focused release-closure tests: 38 passed. Full backend Pytest: 234 passed with one existing Starlette TestClient deprecation warning. Compileall, ESLint, TypeScript, Next.js production build, and `git diff --check` passed.
- Parent-led source, staging, ZIP, and frontend-build security review found no critical regression. FORMAL SECURITY SCANNER: NOT EXECUTED because the formal desktop scan service was unavailable.

External limitations remain explicit: live PostgreSQL, PostgreSQL-native backup/restore, external durable Storage, external Notification delivery, reverse proxy, TLS termination, and production process supervision were not executed or remain operator/provider-owned. Binary Media and authorization presets remain intentionally unsupported/deferred.

## Post-release Media authoring improvement

- Added a bounded Media-owned upload contract for signature-validated images, videos, PDFs, text/structured documents, and OOXML documents up to 10 MB while retaining Storage ownership and hiding physical paths.
- Added authenticated preview for private Admin media, public delivery only for explicitly published/unlisted media, `nosniff` responses, document download disposition, image/video previews, prior-upload listing, and name/description/label/type/visibility filtering.
- SVG, executable/unknown formats, image/video transformations, and browser deletion remain unsupported.

Architecture review: PASS. No ownership change, duplicate infrastructure, automatic migration/installation, hidden authorization, universal administrator, marketplace, remote execution, business feature, or Phase 27 functionality was introduced.

Phase 26 gate: PASS. Favorite CMS 0.1.0 is release ready within the documented operator/provider boundaries. Phase 27 was not started.

## Administration and local extension package expansion

Status: In progress on the current development branch; release remains `0.1.0`.

- Added UserEngine role membership/listing contracts, Authentication-owned password reset, account enable/disable, and permission-filtered Admin Users APIs/UI. Permanent deletion remains intentionally unavailable so identity/audit ownership is preserved.
- Added PermissionEngine-owned role definitions, protected built-in roles, custom role lifecycle, explicit permission assignment, and a readable Admin permission matrix. `site-owner` contains the fixed current administration grants explicitly; it never bypasses PermissionEngine and future grants require a deliberate release change.
- Added secret-free AuditEngine records for sensitive administration and extension lifecycle actions.
- Added Storage-scoped local Theme/Plugin ZIP validation, staging, install, manual update, rollback, and inactive uninstall. Uploaded Plugins remain declarative-only and executable content is rejected; there is no sandbox, marketplace, remote download, or arbitrary code loading.
- Added four deterministic migrations: User role membership, Permission role definitions, Audit records, and Extension package registry.
- Added Users, Roles & permissions, Theme/Plugin upload, update, and uninstall UI through the existing Next.js → FastAPI → API/Permission → owner transport.
- Built-in roles are inspectable but release-managed: Admin cannot rename them, delete them, or silently narrow their explicit grants. Operators cannot disable their current identity or remove their own `site-owner` membership.
- New and reset passwords are validated by Authentication on the backend before related User state is created; the Admin minimum is 12 characters.
- Uploaded Theme HTML/CSS remains presentation-only and rejects executable browser content or external stylesheet loading; uploaded Plugins remain non-executable declarative packages.

## Application and isolated Tool Plugin foundation

Status: Implemented on the current development branch; the release version remains `0.1.0`.

- Added a generic Domain Engine with Plugin-owned schemas, bounded fields, explicit CRUD permissions, durable records, restart preservation, and generated Admin management under **Extensions → Applications**. Domain Plugins never receive Database or Storage access.
- Added a generic Tool Engine with validated inputs, durable jobs, normalized status/cancellation, and an operator-configured fixed Worker gateway. Plugins cannot select destinations, read Worker credentials, spawn processes, or access network/Configuration directly.
- Added the Core-owned `[favorite-tool id="..."]` rendering contract and generic Tool job API through the existing Rendering, Routing, API, Authentication, and Permission owners.
- Extended uploaded declarative Plugin packages with schema-versioned permission, entity, and Tool contributions. Packages remain inactive by default and executable files remain prohibited.
- Added per-service capability enforcement to Plugin public facades and owner-scoped cleanup for Permission, Domain, and Tool registrations. Durable records, jobs, and approved lifecycle state remain available for safe reactivation.
- Added two deterministic migrations: `platform.domain.001` and `platform.tool.001`; together with the existing administration migrations, the current authoritative migration count is 16.

## Isolated OCR/direct-media Worker foundation

- Added an optional separately deployed `favorite_worker` service with authenticated fixed-operation endpoints for Bengali/English image OCR and allowlisted direct HTTPS media retrieval.
- The Worker enforces bounded inputs, file counts through one-job requests, download size/time/concurrency limits, exact operator host allowlisting, public-IP resolution, redirect rejection, media signature validation, safe filenames, fixed OCR language choices, and a fixed `shell=False` Tesseract invocation.
- Added inactive-by-default declarative `favorite.plugin.ocr` and `favorite.plugin.direct-media` packages. Both require explicit Plugin capabilities and per-operation Permission grants; neither selects executable modules, commands, providers, environment values, or private services.
- Added distribution coverage and a developer guide for Tool Workers, declarative Plugins, presentation-only Themes, tests, packaging, and prohibited extension behavior.
- Public anonymous Tool execution, private CMS Media handoff, arbitrary media-page extraction, platform/DRM bypass, in-flight job recovery, automatic artifact retention, and external OCR/download providers remain intentionally unsupported.
- No OCR, downloader, commerce, payment, email, or production Worker implementation was added. A real Tool Worker remains a separately deployed, authenticated, resource-limited operator responsibility.

Validation:

- Focused Domain/Tool/Plugin/Admin contract tests: 23 passed. Full backend Pytest: 256 passed with the existing Starlette TestClient deprecation warning.
- ESLint, TypeScript, Python compileall, Next.js production build, distribution regression tests, and `git diff --check` passed.
- Repository Playwright exercised 14/14 real workflows, including the generated Applications Admin UI; all assertions completed before the known Windows child-process teardown delay.
- Clean extraction, fresh Python installation, `pip check`, 16 explicit migrations, zero pending migrations, explicit installation, production backend/Theme startup, frozen frontend installation/build/startup, and 31/31 clean-candidate browser assertions passed.
- Source/package review found no arbitrary uploaded execution, Plugin-selected network destination, private Database/Storage/Configuration access, hidden grant, duplicate Route/API infrastructure, or credential storage. FORMAL SECURITY SCANNER: NOT EXECUTED.
