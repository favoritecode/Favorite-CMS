# Favorite Example Plugin

`favorite.plugin.example` version `1.0.0` is the bundled, first-party reference
Plugin. It is deliberately a small real feature, not a business module.

## Package and trust model

The package contains only `plugin.json`, `contributions.json`, and this package's
README. Discovery validates metadata and never imports or executes package code.
The platform's fixed `reference-message` declarative adapter validates the complete
contribution schema before binding the runtime. No package-selected callable,
module, filesystem path, or service name is accepted.

Activation is explicit. The operator must review and grant exactly these declared
capabilities:

- `admin.register`
- `api.register`
- `rendering.register`
- `routing.register`
- `settings.access`

Requested capabilities are not permissions or role grants. The existing
`admin.extensions.manage` Permission contract independently protects the Plugin's
Admin module and API operation. Authentication never implies authorization.

## Public contracts used

- Plugin Engine: discovery, binding, activation, deactivation, update rollback.
- Settings Engine: durable `PLUGIN`-scoped message state.
- Routing Engine: owner-scoped `/plugins/example` presentation route.
- API Engine: owner-scoped `/api/plugins/example` GET/PATCH operation.
- Rendering Engine: owner-scoped template and presentation operation.
- Admin Application: owner-scoped module registration.
- Permission Engine: authorization of the Admin/API operation.

Deactivation unregisters the Plugin's API operation, Route, rendering resources,
presentation operation, Admin module, and active Setting definition. The stored
Setting value is retained as domain state, so an explicit activation after restart
can restore it. Failed candidate activation removes candidate contributions and
restores the prior active runtime.

The Plugin has no direct Database, Storage Provider, Authentication implementation,
Configuration/environment, or filesystem access. It provides no dynamic Python
loading, marketplace, remote download, archive installation, or sandbox claim.

## Distribution

The validated data package is included in the base distribution allowlist. It is
installed but inactive by default and receives no implicit capability grant. No new
distribution archive is produced merely by maintaining this package.
