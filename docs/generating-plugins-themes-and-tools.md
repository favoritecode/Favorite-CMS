# Generating Plugins, Themes, and Tools

This document contains copy-ready implementation prompts for extending Favorite CMS from a clean GitHub checkout. Always inspect current public contracts and tests before changing code. Favorite CMS is extensible, but it is not an arbitrary executable package host.

## Choose the correct extension

- Structured CMS feature, shop catalog, products, services, directories, or forms: declarative Application Plugin using Domain/API/Admin/Rendering contracts.
- Public presentation and layouts: presentation-only Theme.
- OCR, conversion, direct-media retrieval, or other resource-heavy operation: declarative Tool Plugin plus a reviewed fixed operation in the isolated Worker.
- New schema: only through Migration-owned contracts.
- Payment, delivery, email, or external vendor integration: only after an approved provider-neutral owner contract exists.

Never give a Plugin or Theme direct Database, Storage-provider, Configuration/environment, filesystem, process, Authentication, Permission, or private Core access.

## Prompt: create a declarative Plugin

Copy this prompt and replace the placeholders:

```text
Work in the current Favorite CMS repository and current branch.

Create a new declarative Favorite CMS Plugin.

Plugin name: <PLUGIN NAME>
Plugin ID: favorite.plugin.<plugin-id>
Version: 1.0.0
Purpose: <GENERIC FEATURE DESCRIPTION>
Required entities/data: <FIELDS AND TYPES>
Required Admin UI: <PAGES, FORMS, ACTIONS>
Required public presentation: <ROUTE, BLOCK, OR SHORTCODE>
Required Tool operation: <NONE OR EXACT OPERATION>

Before implementation inspect PluginEngine, DomainEngine, ToolEngine, Routing,
API, Rendering, Admin, Authentication, Permission, Settings, Media, Storage,
Migration, existing Plugin packages, and their tests.

Preserve Core architecture and every ownership boundary. Do not create a second
Router, API registry, Renderer, Admin framework, Authentication, Permission,
Database, Storage, Settings, Migration, Plugin runtime, or Worker gateway.

Use this data-only package structure:

plugins/favorite.plugin.<plugin-id>/
  plugin.json
  contributions.json
  README.md

The Plugin must be discovered but inactive by default. plugin.json must declare
its stable reverse-domain ID, version, Core compatibility, dependencies, and
only the minimum required capabilities.

Define only required canonical permissions, for example:

favorite.plugin.<plugin-id>.read
favorite.plugin.<plugin-id>.create
favorite.plugin.<plugin-id>.update
favorite.plugin.<plugin-id>.delete
favorite.plugin.<plugin-id>.execute

Backend PermissionEngine remains authoritative. Do not add hidden grants,
frontend-only checks, wildcard authorization, a master password, or an implicit
administrator. Capability approval and operation permission must be explicit.

Use DomainEngine for supported structured records, Settings/Plugin-scoped state
for supported configuration, and existing Routing/API/Rendering/Admin
contribution contracts. Never query or modify Database tables directly.

The package must not declare or select Python/JavaScript modules, imports,
callables, commands, subprocesses, providers, sockets, environment variables,
filesystem paths, arbitrary URLs, or private services.

If a heavy operation is required, submit a validated bounded job through
ToolEngine. Do not perform network, filesystem, process, OCR, conversion, or
download work inside the Plugin.

Deactivation must remove Plugin-owned Domain/Tool/API/Route/Rendering/Admin
registrations. Failed activation must preserve the previous valid state.
Persistent state must remain owner-scoped and restart-safe where the public
contract supports it.

Add focused tests for manifest validation, inactive default, capability denial,
explicit approval, authorization denial, activation, deactivation, cleanup,
restart state, invalid input, failure rollback, private-service isolation, and
distribution inclusion. Add real Playwright coverage for user-visible workflows
using Next.js -> FastAPI -> Routing/API -> Authentication/Permission -> owner.
Do not intercept HTTP or mock production success responses.

Audit eval/exec, subprocess, dynamic imports, arbitrary callables, filesystem,
environment, Database/Storage bypass, unsafe HTML, redirects, SSRF, secrets,
hidden grants, and duplicate infrastructure.

Run focused/full backend tests, compileall, ESLint, TypeScript, Next.js build,
real browser tests where changed, distribution validation, reproducible builds,
and git diff --check. Report exact files, capabilities, permissions, tests,
limitations, and architecture validation. Do not push until requested.
```

## Prompt: create a fixed Worker Tool

Use this only when the operation cannot safely run as a declarative data contract:

```text
Create a capability-gated declarative Tool Plugin and one fixed isolated
Favorite Tool Worker operation.

Tool name: <TOOL NAME>
Plugin ID: favorite.plugin.<plugin-id>
Tool ID: favorite.tool.<tool-id>
Inputs: <BOUNDED INPUT FIELDS>
Output: <NORMALIZED RESULT>

The Plugin must remain data-only. It may only register the Tool contract and
submit validated jobs through ToolEngine. It cannot choose a Worker URL,
provider, command, executable, module, callable, import, filesystem location,
Database, Storage provider, or environment value.

WorkerEngine must implement only the exact reviewed Tool ID. Authenticate CMS
requests with server-only Configuration. Add strict input schema, maximum
length/size, timeout, concurrency, cancellation, normalized failure, and safe
result limits. Unknown Tool IDs and unexpected fields must fail closed.

For outbound retrieval use HTTPS, an exact operator host allowlist, validated
global IP resolution pinned to the TLS connection, hostname certificate
verification, no URL credentials, no redirects, bounded streaming, media
signature validation, and safe filenames. Never allow private/local addresses,
wildcard destinations, user-selected webhooks, or SSRF-capable endpoints.

For a subprocess, use only a fixed operator-installed executable with a fixed
argument shape, validated enumerated options, generated temporary paths,
shell=False, captured bounded output, timeout, and cleanup. Plugin/user input
must never select a command or arbitrary argument.

Never bypass platform access controls, authentication, copyright protection, or
DRM. A direct-media Tool must accept only direct authorized media resources; it
must not resolve protected video pages.

Keep public anonymous execution disabled unless explicit rate-limit, quota,
abuse-control, and public artifact-delivery contracts already exist. Document
Worker restart, job durability, artifact retention, private Media handoff, and
external-provider limitations honestly.

Test Worker authentication, unknown operations, validation, private-IP and DNS
rebinding protection, redirects, size/type/signature checks, fixed command use,
timeout, cancellation, safe errors, Plugin capability/permission denial,
lifecycle cleanup, HTTP transport, and package inclusion. Run the complete
regression and security gates.
```

## Prompt: create a Theme

```text
Work in the current Favorite CMS repository and inspect ThemeEngine, Rendering,
Favorite Starter Theme, Theme manifests/resources, public presentation models,
and existing tests before implementation.

Theme name: <THEME NAME>
Theme ID: favorite.theme.<theme-id>
Version: 1.0.0
Design direction: <COLORS, TYPOGRAPHY, LAYOUT>

Required presentation:
- homepage
- Content listing
- Content detail
- Search
- safe empty and missing-resource states
- header/navigation/hero/footer
- desktop, tablet, and mobile navigation

Use the existing Theme package and manifest contract. Declare ID, name, version,
Core compatibility, and every permitted resource. Keep all paths relative and
within resource/file/size limits.

The Theme is presentation-only. It may consume only Rendering-provided safe
public models. It cannot access Database, SQLAlchemy, Storage/provider paths,
filesystem, Configuration/environment, Authentication, Permission, Settings
internals, Plugin private state, network clients, processes, or private Core
services. Do not add executable server code or arbitrary Theme JavaScript.

Escape user-controlled values. Render approved rich content only through the
existing sanitization contract. Preserve published/private isolation and safe
SEO projection behavior.

Implement semantic headings, landmarks, accessible names, keyboard navigation,
visible focus, screen-reader status text, sufficient contrast, responsive
layouts, and safe form/error states. Do not invent business-specific content or
missing Menu/Site contracts.

Activation failure must preserve the previous valid Theme. Favorite Starter
Theme must remain recoverable as fallback. Reject missing/undeclared/oversized
resources, absolute paths, traversal, and symlinks.

Test discovery, manifest/compatibility, resources, traversal/symlink rejection,
activation, rendering, failure rollback, fallback, homepage, listing/detail,
Search, missing resources, responsive layouts, keyboard behavior, accessibility,
and distribution inclusion. Run backend regression, lint, TypeScript, production
build, real Playwright transport, reproducible distribution, and diff check.
Report exact files, resources, tests, limitations, and architecture validation.
```

## Package and release checklist

1. Keep the extension inactive until an authorized operator reviews capabilities.
2. Validate compatibility and dependencies before activation.
3. Add runtime files to the explicit distribution allowlist only after tests pass.
4. Exclude tests, secrets, populated `.env`, databases, Storage/spool contents, caches, bytecode, `.next`, `node_modules`, logs, and Playwright artifacts.
5. Build twice and require identical SHA-256.
6. Extract into a clean directory and verify explicit migration/installation, backend/frontend startup, real browser transport, extension activation/deactivation, failure rollback, and cleanup.
7. Never claim external PostgreSQL, Storage, Notification, OCR, download, TLS, proxy, or provider validation unless it actually ran.

See also:

- `docs/extension-development.md`
- `docs/application-plugin-foundation.md`
- `docs/tool-worker-and-extension-guide.md`
- `docs/vps-and-local-hosting.md`
