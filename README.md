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

On POSIX systems use `.venv/bin/python`. Repeat `--authorization` for every explicitly selected authorization. Favorite CMS creates no universal administrator role and grants nothing implicitly. Installation is idempotent and a failed installation may be retried without silently replacing an existing initial identity.

Build the source-distributed frontend:

```text
cd frontend
pnpm install --frozen-lockfile
pnpm run build
```

Start the backend and frontend:

```text
uvicorn backend.main:app --host <internal-host> --port <backend-port>
pnpm start -- --hostname <internal-host> --port <frontend-port>
```

Set the server-only `FAVORITE_API_URL` for Next.js. Do not put database URLs, Authentication secrets, or credentials in `NEXT_PUBLIC_*` variables. Normal application startup performs neither migration nor installation.

After both processes are running, open the Next.js Admin login at `http://<frontend-host>:<frontend-port>/admin/login`. Public CMS presentation is served by FastAPI under `/site/*`; the starter homepage is `/site/welcome`. Your reverse proxy may present those paths on one public origin while preserving the documented backend/frontend ownership split.

The bundled Plugins are discovered but inactive by default. Activate them from **Admin → CMS management → Plugins and Themes**, review their declared capabilities, and explicitly approve those capabilities before activation. The bundled Favorite Starter Theme is activated by installation. Favorite CMS 0.1.0 does not include a marketplace, remote package installer, binary-image upload UI, or a universal administrator role.

Operators explicitly granted `admin.diagnostics.view` receive a redacted system-status dashboard and detailed Diagnostics page. Public Health remains minimal. The private view reports only owner-confirmed states and provider types—never configuration values, Database URLs, Storage paths, credentials, Notification payloads, or stack traces. It does not perform migration, installation, update, or recovery actions.

See [distribution documentation](docs/distribution.md), [deployment runbook](docs/runbooks/deployment.md), and [operations runbook](docs/runbooks/operations.md).

## Development

```text
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
cd frontend
pnpm install --frozen-lockfile
```

The architecture documents in `docs/` remain the source of truth. Plugins and Themes consume public contracts and must not replace Core infrastructure.
