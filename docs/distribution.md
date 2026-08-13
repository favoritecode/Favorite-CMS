# Favorite CMS production distribution

## System requirements

- Python 3.12 or newer
- Node.js 22
- pnpm compatible with the committed lockfile
- PostgreSQL for production
- An operator-managed durable filesystem mount for the `mounted` Storage provider, or a separately approved provider adapter
- A process host for FastAPI and a process host for the Next.js server

## Package model

The distribution ships backend and frontend source plus locked dependency metadata. It does not ship development environments, `node_modules`, tests, local databases, or generated Storage. Build timestamps are excluded and ZIP entries use a fixed timestamp.

Build the frontend during deployment:

```text
cd frontend
pnpm install --frozen-lockfile
pnpm run build
pnpm prune --prod
```

The build host needs the declared development build tools. Runtime uses only the pruned production dependencies and `.next` output.

## Configuration

Copy `.env.production.example` into a secure environment-specific configuration system. Do not place the populated file inside the application package or public directory.

Required production values include a PostgreSQL SQLAlchemy URL, a high-entropy Authentication signing secret, the persistent mounted Storage root, and `FAVORITE_ACTIVE_THEME=favorite.theme.starter`. `FAVORITE_API_URL` is server-only Next.js configuration. Never place backend credentials in `NEXT_PUBLIC_*` variables.

The `mounted` Storage provider is vendor-neutral. Its configured root must be a durable filesystem supplied, backed up, permissioned, and monitored by the operator. Local ephemeral disk is not an approved production substitute.

## Explicit migrations

From the extracted package root:

```text
favorite-cms migrate
favorite-cms status
```

Normal backend startup never applies migrations.

## Installation

The caller chooses the initial role and every authorization. No administrator role or implicit grant exists. Repeat `--authorization` for each required permission using:

```text
permission-id:owner:action:resource-type
```

Example structure (identifiers must match registered platform permissions):

```text
favorite-cms install --email <address> --display-name <name> --role <caller-role> --authorization <permission:owner:action:resource> --password-stdin
```

For a first operator who should see every bundled management area, the caller may explicitly repeat
`--authorization` with the five current Admin contracts below. This is an operator choice, not a
built-in administrator role or implicit grant:

```text
admin.content.manage:application.admin.platform:manage:admin_content
admin.media.manage:application.admin.platform:manage:admin_media
admin.settings.manage:application.admin.platform:manage:admin_settings
admin.extensions.manage:application.admin.platform:manage:admin_extensions
admin.diagnostics.view:application.admin.platform:view:admin_diagnostics
platform.content.create:application.admin.platform:create:content
platform.content.read:application.admin.platform:read:content
platform.content.update:application.admin.platform:update:content
platform.content.delete:application.admin.platform:delete:content
platform.content.publish:application.admin.platform:publish:content
platform.content.archive:application.admin.platform:archive:content
platform.media.create:application.admin.platform:create:media
platform.media.read:application.admin.platform:read:media
platform.media.update:application.admin.platform:update:media
platform.media.delete:application.admin.platform:delete:media
platform.setting.read:application.admin.platform:read:setting
platform.setting.write:application.admin.platform:update:setting
```

The first five permissions expose Admin modules. The remaining permissions authorize the corresponding owning Engine operations. Selecting only a subset produces an intentionally restricted operator.

These tuples are intentionally explicit and technical in `0.1.0`: the installer does not infer an administrator role or hidden grant set. A future permission-preset UX would require a separately documented contract. Operators should retain a reviewed deployment-specific list rather than copying permissions they do not intend to grant.

Provide the password through standard input or omit `--password-stdin` for a hidden prompt. The command never prints the password, token, hash, signing secret, or database URL. Repeated installation returns the persisted installed state without replacing the initial identity.

All operator commands return exit code `0` on success. Validation, configuration, migration, or installation failures return a nonzero exit code with a redacted error category; sensitive configuration values and submitted credentials are not echoed. Run `favorite-cms --help` or the corresponding command `--help` before automation.

## Runtime

Backend:

```text
uvicorn backend.main:app --host <internal-host> --port <backend-port>
```

Frontend:

```text
cd frontend
pnpm start -- --hostname <internal-host> --port <frontend-port>
```

A provider-neutral HTTP ingress must preserve these ownership routes:

- backend CMS presentation routes such as `/site/*` go to FastAPI, then Routing and Rendering;
- backend API and Health routes go to FastAPI;
- `/admin/*`, `/explore/*`, and frontend application pages go to Next.js;
- Next.js server routes call FastAPI using `FAVORITE_API_URL`.

TLS termination, proxy software, process supervision, and hosting vendor are environment choices.

## First operator walkthrough

1. Open `/admin/login` on the Next.js frontend and sign in with the identity created by `favorite-cms install`.
2. The dashboard and navigation show only explicitly authorized modules.
3. Use `/admin/manage` to create draft Content, publish it, store supported text/document Media, edit the site-title Setting, review Plugin capabilities, and inspect Theme/Health status.
4. Visit the FastAPI public CMS at `/site/welcome`; published Content appears under `/site/content` and Search is available under `/site/search/<query>`.
5. Bundled Plugins are inactive by default. Review the displayed version and capabilities before explicitly activating each Plugin. Plugin state stored through Settings survives deactivation/reactivation; route and presentation contributions are removed while inactive.
6. Sign out from Admin and verify protected pages require authentication again.

The current browser Media surface stores bounded UTF-8 text/document resources and shows safe metadata through Media → Storage. Binary image upload, transformation, and browser Media deletion are not part of the `0.1.0` public Admin contract. The package includes one production Starter Theme; invalid-package rejection and previous-theme preservation are Engine-level lifecycle guarantees, not a deliberately broken package exposed to operators.

## Operational validation

Require `/health/live`, `/health/ready`, migration status, Admin authentication/authorization, and public Rendering smoke checks before traffic cutover. Use Update Engine for platform/extension update coordination and Recovery Engine for supported backup/restore operations.

PostgreSQL backup and restore is not implemented by Favorite CMS. Operators must use an approved PostgreSQL-native backup process and must not claim it as platform-verified Recovery support. The mounted Storage root requires an environment-owned backup policy.

Update validation in `0.1.0` supports deterministic extension compatibility, checksum validation, locking, migration coordination, state preservation, and failure rollback through the Update Engine. This does not constitute a separate `0.2.0` release or a remote update service. Test an approved future package and recovery point before production activation.

## Removal

Stop backend/frontend processes, preserve or remove Database and Storage according to the operator's retention policy, then remove the extracted application directory. Removing application files does not remove an external PostgreSQL database or mounted Storage data.

## Security

Never package populated `.env` files, credentials, local databases, generated Storage, test fixtures, or logs. Protect the installer from untrusted users. Plugin and Theme packages must pass their owning Engine validation and must never be loaded merely because arbitrary code is present on disk.

Release validation includes repository-controlled source, package-content, credential, path-boundary, and browser-session audits. A formal external security scanner is not bundled with Favorite CMS and must be reported as **NOT EXECUTED** unless an operator or release environment actually runs one successfully; local audit results are not a substitute claim for formal scanner coverage.

Authorized operational diagnostics are included in the runtime. Public Health responses remain minimal; the Admin diagnostics contract reports safe status categories and configuration presence only. It does not expose values or replace explicit `favorite-cms migrate`, `favorite-cms install`, Update Engine, Recovery Engine, or provider-owned operational procedures.
