# Favorite CMS 0.1.0

Favorite CMS is a modular, API-first CMS distributed as a source-build package. Core owns composition; platform Engines retain their documented data and infrastructure boundaries; Admin is an authenticated API client.

## Production requirements

- Python 3.12+
- Node.js 22
- pnpm compatible with the committed lockfile
- PostgreSQL for production
- A durable operator-managed mount for the `mounted` Storage provider, or another separately approved Storage adapter
- Separate FastAPI and Next.js process hosts behind a provider-neutral HTTP ingress

## Install from the distribution

Configure production values using `.env.production.example` as a key reference. Never place a populated environment file in the package or public directory.

```text
python -m venv .venv
.venv/Scripts/python -m pip install .
favorite-cms migrate
favorite-cms install --email <address> --display-name <name> --role <caller-role> --authorization <permission:owner:action:resource> --password-stdin
favorite-cms status
```

On POSIX systems use `.venv/bin/python`. Repeat `--authorization` for every explicitly selected authorization. Favorite CMS has no authorization bypass: every decision still goes through PermissionEngine. The protected built-in `site-owner` role is the transparent exception to manual tuple entry: it receives the fixed, inspectable `0.1.0` administration permission set as explicit grants. It is not a wildcard, and future permissions require a deliberate migration/update decision. Other roles receive nothing implicitly. Installation is idempotent and a failed installation may be retried without silently replacing an existing initial identity.

Content management requires both the Admin route permission and the ContentEngine action permissions. Select them explicitly during initial installation by repeating `--authorization`, or add only the missing grants to an existing role with this operator command:

```powershell
.venv\Scripts\python.exe -m backend.cli grant-role --role <content-role> `
  --authorization admin.content.manage:application.admin.platform:manage:admin_content `
  --authorization platform.content.create:application.admin.platform:create:content `
  --authorization platform.content.read:application.admin.platform:read:content `
  --authorization platform.content.update:application.admin.platform:update:content `
  --authorization platform.content.delete:application.admin.platform:delete:content `
  --authorization platform.content.publish:application.admin.platform:publish:content `
  --authorization platform.content.archive:application.admin.platform:archive:content
```

`grant-role` is explicit and idempotent. It validates each permission against its registered owner and grants nothing beyond the repeated `--authorization` values.

Build the source-distributed frontend:

```text
cd frontend
pnpm install --frozen-lockfile
pnpm run build
```

Start the backend and frontend:

```text
uvicorn backend.main:app --host <internal-host> --port <backend-port>
pnpm start --hostname <internal-host> --port <frontend-port>
```

Set the server-only `FAVORITE_API_URL` for Next.js. Do not put database URLs, Authentication secrets, or credentials in `NEXT_PUBLIC_*` variables. Normal application startup performs neither migration nor installation.

After both processes are running, open the Next.js Admin login at `http://<frontend-host>:<frontend-port>/admin/login`. Public CMS presentation is served by FastAPI under `/site/*`; the starter homepage is `/site/welcome`. Your reverse proxy may present those paths on one public origin while preserving the documented backend/frontend ownership split.

The bundled Plugins are discovered but inactive by default. Activate them from **Admin → Extensions → Plugins**, review their declared capabilities, and explicitly approve those capabilities before activation. Once explicitly activated, the active state and approved capabilities persist across application and PC restarts. Active Plugin configuration is available both from the Plugin card and **System → Settings**. Website Settings include title, tagline, description, validated public origin, and registered default locale. **Administration → Users** manages identity state and role assignment; **Administration → Roles & permissions** exposes canonical grants grouped by subsystem. The bundled Favorite Starter Theme is activated by installation.

Declarative Application Plugins may register permission-scoped Domain schemas and isolated Tool contracts without receiving Database, Storage, Configuration, filesystem, network, or process access. Authorized Domain records are managed under **Extensions → Applications**. Public Tool forms use `[favorite-tool id="..."]` and delegate execution to one fixed operator-configured Worker gateway; without that separately deployed gateway they remain safely unavailable. See [Application and Tool Plugin foundation](docs/application-plugin-foundation.md).

The optional isolated Tool Worker now provides fixed OCR and allowlisted direct-media retrieval operations for the bundled, inactive-by-default OCR and Direct Media Plugins. It is not an arbitrary Plugin runtime or a platform/DRM bypass. Setup, operational limits, and complete declarative Plugin/Theme authoring instructions are in [Tool Worker, Plugin, and Theme guide](docs/tool-worker-and-extension-guide.md).

Authorized operators can install local Theme ZIPs and declarative Plugin ZIPs from the Themes and Plugins pages. Uploads are validated before controlled temporary extraction and persisted through scoped Storage. Installation never activates a package. Uploaded Plugins cannot contain executable Python, JavaScript, native binaries, shell scripts, or package-selected callables; ZIP validation is not represented as a code sandbox. Updates require the same package ID, a newer version, valid compatibility/dependencies, and preserve the previous runtime on failure. Active extensions and the bundled Starter Theme cannot be uninstalled. Media supports bounded JPEG, PNG, WebP, GIF, MP4, WebM, PDF, plain-text/structured-text, DOCX, XLSX, and PPTX uploads through Media Engine → Storage; executable and unknown formats remain rejected. Favorite CMS 0.1.0 still has no marketplace, remote downloader, image transformation pipeline, or arbitrary binary execution.

Operators explicitly granted `admin.diagnostics.view` receive a redacted system-status dashboard and detailed Diagnostics page. Public Health remains minimal. The private view reports only owner-confirmed states and provider types—never configuration values, Database URLs, Storage paths, credentials, Notification payloads, or stack traces. It does not perform migration, installation, update, or recovery actions.

See [distribution documentation](docs/distribution.md), [deployment runbook](docs/runbooks/deployment.md), and [operations runbook](docs/runbooks/operations.md).
For an end-to-end Ubuntu VPS layout and the existing Windows local/autostart flow, see [VPS and local hosting](docs/vps-and-local-hosting.md).

## Development

```text
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
cd frontend
pnpm install --frozen-lockfile
```

The architecture documents in `docs/` remain the source of truth. Plugins and Themes consume public contracts and must not replace Core infrastructure.
