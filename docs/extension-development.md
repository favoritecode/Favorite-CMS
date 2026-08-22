# Favorite CMS extension development

This guide describes the fixed public extension surface in Favorite CMS `0.1.0`. It does not authorize arbitrary Python loading, package-selected callables, private service access, or unrestricted filesystem access.

## Theme packages

A Theme lives under `themes/<theme-id>/` with a validated `theme.json` declaring identity, version/Core compatibility, dependencies, templates, layouts, components, and assets. Every referenced resource must remain inside the package and pass traversal, symlink, and resource-limit checks.

Themes are presentation-only. Theme Engine owns discovery, validation, activation, and resources; Rendering resolves declared resources through Theme → Plugin → platform fallback. Activation failure preserves the previous Theme. Themes cannot register backend APIs, query Database or Storage, inspect Authentication/Permission, read environment configuration, or execute package code.

Create a first-party Theme using the structure of `favorite.theme.starter`, a unique manifest identity, fully declared data-only resources, and tests for discovery, validation, activation, fallback, rollback, missing resources, accessibility, and responsive presentation.

## Declarative first-party Plugin packages

A bundled Plugin contains `plugin.json`, `contributions.json`, and `README.md`. The manifest declares identity, version, compatibility, dependencies, and requested capabilities. Contributions use a fixed schema, supported contribution kind, title, and activation test mode.

Discovery reads data only. Plugin Engine binds a fixed platform-owned runtime for an allowlisted first-party identifier; it never imports code from the package. Capabilities are shown and must be approved exactly before activation. Admin visibility is not authorization: protected Plugin APIs independently use Authentication and Permission.

Public services are scoped Settings, Content, Media, Search, Localization, Menu, SEO, Events, Queue, Notifications, Permission evaluation, and Plugin-scoped Routing/API/Rendering/Admin/Health façades. Plugins cannot resolve private services or create registries.

Lifecycle is discovery → manifest/compatibility/dependency validation → explicit binding → registration → activation. Deactivation unregisters owner-scoped Routing, API, Rendering, Admin, and Notification contracts. Failed activation cleans partial contributions; failed update restores the previous runtime and state. State belongs in an approved owner-scoped contract such as Settings.

## Content SEO projection

Content Engine owns optional per-resource SEO metadata. Authorized callers set bounded `ContentSeoMetadata` through Content authorization, including an optional SEO title, meta description, canonical path, robots value, and Open Graph fields. Consumers receive `ContentSeoProjection` only for published Content and a validated HTTP(S) public origin. An empty SEO title falls back to the Content title. Canonical and Open Graph image values are relative paths; no fetch occurs. SEO Plugin escapes projected values before presentation.

## Contact notification delivery

Contact Plugin validates and stores bounded submissions, then submits a provider-neutral request to Notification Engine. Notification owns recipient, channel, payload, durable status, attempts, availability, and failure normalization; its bounded delivery ledger persists through the existing Settings contract and is restored after restart. Without an approved `email` adapter, delivery remains pending. This release contains no SMTP, webhook, arbitrary URL, provider credentials, or external-delivery claim.

## Minimal package examples

A minimal Theme is data-only and keeps every declared resource inside its package:

```text
themes/favorite.theme.sample/
  theme.json
  layouts/base.html
  templates/page.html
  components/header.html
  components/footer.html
  assets/theme.css
```

Its manifest declares `id`, `type: theme`, name, semantic version, Core compatibility, dependencies, and every resource reference. References are logical package-relative paths. Missing required resources, traversal, symlinks, incompatible versions, and resource-limit violations reject activation while preserving the previous valid Theme.

A minimal declarative first-party Plugin is:

```text
plugins/favorite.plugin.sample/
  plugin.json
  contributions.json
  README.md
```

```json
{"schemaVersion":1,"kind":"supported-fixed-kind","title":"Sample","activation":"normal"}
```

Only fixed platform-supported first-party identifiers and contribution kinds can bind a platform-owned runtime. A package cannot name a Python module, callable, service, provider, command, URL, or private Engine. The manifest lists exact compatibility, dependencies, and required capabilities. Admin displays required versus granted capabilities and normalized lifecycle failures; nothing is inferred from a user role.

Public Route contributions use the Plugin-scoped Routing facade, API operations use the Plugin-scoped API facade, presentation uses Rendering resources/operations/decorators, and Admin modules use the Plugin-scoped Admin facade. State uses an approved owner-scoped contract such as Settings. Deactivation must remove every owned Route, API operation, rendering resource/decorator, Admin module, Setting definition, health contribution, and Notification contract. Partial registration or activation failure triggers cleanup; update failure restores the previous valid runtime and state.

## Extension testing and packaging

## Local Admin ZIP installation

Authorized operators may upload a local ZIP through **Themes → Add Theme** or **Plugins → Add Plugin**. The API enforces separate explicit `platform.extension.install`, `activate`, `deactivate`, `update`, and `uninstall` permissions in addition to Admin module visibility. Installation and activation are separate.

The package boundary limits the compressed archive to 5 MB, extracted content to 20 MB, and entries to 500. It rejects malformed ZIPs, absolute paths, drive-qualified paths, `..` traversal, case-conflicting/duplicate names, symlinks/special files, missing or inconsistent manifests, incompatible Core versions, missing dependencies, undeclared Theme resources, and unsafe layouts. Validation and materialization complete before lifecycle registration; the durable archive is stored only in the `extensions/packages` Storage scope.

Uploaded Themes must provide the standard public resource set (`templates/page.html`, `layouts/base.html`, header/footer components, and a declared stylesheet), so Rendering can compose existing public operations without Theme code. Uploaded Plugins are deliberately data-only: `plugin.json`, an optional empty `contributions.json`, README, and license files are accepted. Executable Python/JavaScript/native/shell content and arbitrary declarative contributions are rejected. There is no code sandbox, signing authority, trusted publisher registry, remote repository, or marketplace in `0.1.0`; these are future trust contracts rather than implied security.

Manual update validates identity, semantic version ordering, compatibility, dependencies, and the complete candidate before replacing the runtime. Storage or activation failure leaves the current package intact. An inactive uploaded extension may be uninstalled; the active Theme, active Plugins, bundled packages, and the Starter Theme are protected by lifecycle rules.

Test data-only discovery, manifest validation, Core compatibility, dependency ordering, exact capability denial/approval, activation, deactivation, cleanup, reactivation, restart state, failed-activation rollback, safe API errors, ownership boundaries, Theme fallback, and traversal/symlink rejection. Use real browser transport for user-facing contributions and do not mock away the owning Engine.

Add a distributable first-party extension only through the explicit `distribution/manifest.json` allowlist. Build twice and require identical hashes. Confirm that tests, caches, databases, Storage state, populated environment files, credentials, bytecode, `node_modules`, `.next`, and Playwright artifacts are absent.

## Media boundary

The browser Media contract uses Media → Storage for bounded uploads and a Routing/API-owned binary delivery response. Allowed signatures and extensions are checked for JPEG/PNG/WebP/GIF, MP4/WebM, PDF, text/Markdown/CSV/JSON and OOXML documents, with a 10 MB limit and `nosniff` delivery. SVG/HTML/executable uploads, transformations, arbitrary MIME types and browser deletion remain unsupported.

## Testing and distribution

Test manifests, compatibility, capability denial, lifecycle, cleanup, rollback, restoration, path boundaries, escaping, and real HTTP/browser flows without interception. Add approved packages explicitly to the deterministic distribution manifest. Exclude tests, caches, `node_modules`, `.next`, databases, Storage contents, populated environment files, credentials, keys, and Playwright artifacts. Require byte-identical builds before replacing an artifact.

Extensions may not use `eval`, `exec`, subprocesses, arbitrary imports, unsafe deserialization, client-selected services/callables, remote packages, hidden grants, implicit administrator access, direct Database/Storage-provider access, environment reads, arbitrary scripts/URLs, or duplicate infrastructure.

Friendly permission presets remain future work because no safe preset contract exists. Installation continues to display and accept explicit authorization tuples.
