# First-Party Plugin Suite

Phase 22 adds two public boundaries without changing Plugin lifecycle ownership: Favorite SEO consumes Content-owned published SEO projections, and Favorite Contact submits delivery requests to Notification Engine. See `docs/extension-development.md` for package, lifecycle, capability, security, testing, and distribution guidance. External Contact delivery remains pending without an approved adapter. Browser binary Media and authorization presets remain intentionally unavailable.

The Phase 15 suite contains four independently discovered, inactive-by-default,
data-only Plugin packages. Every package uses explicit operator-approved
capabilities and the Plugin Engine's fixed declarative runtime. Package data cannot
select Python modules, callables, services, scripts, filesystem paths, or providers.

## Favorite SEO

Provides Plugin-scoped site title, meta description, canonical base, robots, and
safe Open Graph metadata. Rendering applies the contribution through an
owner-scoped decorator and removes it on deactivation. Canonical input accepts only
credential-free HTTP(S) origins. Per-content SEO editing is not implemented because
SEO Engine reserves resource/plugin contributions for the registered Content owner;
the Plugin does not bypass that ownership rule.

## Favorite Contact Form

Provides a public, validated contact form and protected Admin configuration.
Submissions have bounded fields, an email grammar, a hidden honeypot field, safe API
errors, and a maximum retained Plugin-scoped history of 100 records. Submissions are
stored with `pending` status through Settings Engine. The form is anonymous and does
not mutate authenticated session state, so the Admin CSRF/session boundary is not
reused. External delivery is not implemented: Notification Engine currently exposes
no approved durable external recipient/provider configuration contract.

## Favorite Sitemap

Projects only Content visible through the public Content query into deterministic
XML. An authenticated, authorized Admin operation configures the validated HTTP(S)
public origin. Routing owns `/sitemap.xml`; Rendering owns XML serialization. No
Database or Route registry is duplicated.

## Favorite Analytics Integration

Supports only `none` and `first-party` provider states. The enabled presentation
contribution is a fixed metadata contract with a strictly validated non-secret site
identifier. No user-supplied script URL, external request, credential, arbitrary
HTML, or commercial vendor integration exists.

## Shared lifecycle and security

All Settings, API operations, Admin modules, Routes, resources, decorators, and
presentation operations are owner-scoped and removed on deactivation. Stored
Settings remain owner-scoped for explicit restart/reactivation. A failing optional
presentation decorator is isolated and cannot make the owning Theme page fail.

The suite has no direct Database, Storage Provider, Authentication implementation,
Configuration/environment, or filesystem access. It uses no dynamic import,
`eval`, `exec`, subprocess, system command, unsafe deserialization, remote download,
or sandbox claim.
