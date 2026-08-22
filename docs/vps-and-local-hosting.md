# VPS and local hosting

This guide deploys the existing Favorite CMS 0.1.0 architecture. It does not add automatic migration/installation, a marketplace, arbitrary Plugin execution, or a vendor-specific provider.

## Supported topology

- Nginx or another operator-selected TLS reverse proxy
- Next.js on `127.0.0.1:3010`
- FastAPI on `127.0.0.1:8020`
- optional fixed-operation Tool Worker on `127.0.0.1:8060`
- PostgreSQL for production
- an operator-backed durable mounted Storage directory
- three separately supervised processes

Declarative Plugins and presentation-only Themes run through their existing Engines. OCR/direct-media Plugins use the fixed Worker. This does not support arbitrary executable Plugin/Theme packages, protected-platform/DRM bypass, or a general remote downloader.

## Ubuntu VPS prerequisites

On a supported Ubuntu host, install Python 3.12+, PostgreSQL, Nginx, Tesseract with English/Bengali data, and Node.js 22 plus pnpm from their approved upstream/package sources. Verify each installed version before continuing.

```bash
python3 --version
node --version
pnpm --version
psql --version
tesseract --version
tesseract --list-langs
```

The Tesseract language list must contain `eng` and `ben`. Create a dedicated unprivileged operating-system account and deploy the verified source ZIP or Git checkout to `/opt/favorite-cms`. Do not run the CMS as root.

```bash
cd /opt/favorite-cms
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install .
.venv/bin/python -m pip check
cd frontend
pnpm install --frozen-lockfile
pnpm run build
```

## Database and Storage

Create a dedicated PostgreSQL database/identity using an operator-selected strong password. Do not copy a password from this guide. Put the SQLAlchemy PostgreSQL URL only in the backend environment file. Create a durable mounted directory such as `/srv/favorite-cms/storage`, owned only by the CMS service account, and include it in the operator backup policy.

Create root-owned, service-readable environment files outside the repository:

- `/etc/favorite-cms/backend.env`: production mode, PostgreSQL URL, mounted Storage, Authentication secret, active Theme, public origin, and the CMS-side Worker URL/token.
- `/etc/favorite-cms/frontend.env`: only `FAVORITE_API_URL=http://127.0.0.1:8020` and non-secret frontend runtime settings.
- `/etc/favorite-cms/worker.env`: Worker token matching the backend value, exact source host allowlist, spool, Tesseract command, limits, timeout, and concurrency.

Generate independent high-entropy Authentication and Worker secrets. Never prefix either with `NEXT_PUBLIC_`. Restrict environment-file permissions, for example `root:favorite-cms` and mode `0640`.

Run schema migration and first installation explicitly before starting services:

```bash
cd /opt/favorite-cms
set -a; . /etc/favorite-cms/backend.env; set +a
.venv/bin/favorite-cms status
.venv/bin/favorite-cms migrate
printf '%s' "$INITIAL_PASSWORD" | .venv/bin/favorite-cms install \
  --email operator@example.com \
  --display-name "Site Operator" \
  --role site-owner \
  --password-stdin
.venv/bin/favorite-cms status
unset INITIAL_PASSWORD
```

Choose the real email/display name/password at deployment time. `site-owner` receives the fixed, inspectable 0.1.0 permission set as explicit grants; it is not an authorization bypass. For another role, supply every authorization tuple explicitly.

## Process supervision

Create three systemd services using the same unprivileged account and these commands:

```text
/opt/favorite-cms/.venv/bin/uvicorn favorite_worker.app:create_app --factory --host 127.0.0.1 --port 8060
/opt/favorite-cms/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8020
/usr/bin/pnpm start --hostname 127.0.0.1 --port 3010
```

Set Worker, backend, and frontend working directories to `/opt/favorite-cms`, `/opt/favorite-cms`, and `/opt/favorite-cms/frontend` respectively. Assign only the matching environment file to each service. Use `Restart=on-failure`, a bounded restart delay, and ordinary systemd logging/rotation. Start Worker first, then backend, then frontend. Normal process startup intentionally does not migrate or install.

After daemon reload and enable/start, require:

```bash
curl --fail http://127.0.0.1:8020/health/live
curl --fail http://127.0.0.1:8020/health/ready
curl --fail http://127.0.0.1:8020/site/welcome
curl --fail http://127.0.0.1:3010/admin/login
```

Worker health additionally requires its bearer token and should be checked from the host without printing that token.

## Reverse proxy and TLS

Bind all application processes to loopback. Configure Nginx so `/admin/`, `/explore/`, `/_next/`, and other Next.js UI resources reach port 3010; `/site/`, `/api/`, and `/health/` reach port 8020. The public root may redirect to `/site/welcome`. Preserve forwarded host/protocol headers, enforce upload/body limits compatible with CMS limits, and use normal proxy timeouts. Obtain and renew TLS using the operator's approved certificate process. Redirect HTTP to HTTPS and set the CMS public origin to the final HTTPS origin.

Do not expose PostgreSQL, the Worker, backend port, or frontend port directly to the internet. A firewall should normally publish only SSH and proxy HTTP/HTTPS.

## Activate extensions

The Starter Theme is installed during explicit CMS installation. Bundled Plugins remain inactive until an authorized operator reviews capabilities and activates them in Admin. For OCR/direct download, approve only their declared capabilities and grant their execute permissions to selected roles. The Worker source-host allowlist must contain each exact host that may serve direct input media. Never use a wildcard allowlist.

## Windows or another local PC

Clone the repository, create `.venv`, install `.[dev]` when developing, run the frozen frontend install/build, and create an ignored sibling `<project>.env` or local `.env` from the example. For OCR install Tesseract 5 with `eng` and `ben` data. Configure the matching CMS/Worker token, local Worker URL, repository-external spool, and exact HTTPS source hosts.

Run the existing unified launcher from PowerShell:

```powershell
.\scripts\start-local-cms.ps1
```

It starts or reuses the configured Worker on 8060, backend on 8020, and frontend on 3010; it does not touch port 3000. To start automatically at Windows sign-in, run an elevated PowerShell once:

```powershell
.\scripts\install-local-cms-autostart.ps1
```

Then visit `http://127.0.0.1:3010/admin/login` and `http://127.0.0.1:8020/site/welcome`.

## Operator-owned limitations

PostgreSQL-native backup/restore, mounted-Storage durability/backup, TLS, reverse proxy, firewall, monitoring, log retention, and process supervision are operator responsibilities. External Notification delivery is not configured by this guide. Worker in-flight jobs are not restart-durable and artifact retention is operator-managed in 0.1.0. Test a complete backup/restore and upgrade rehearsal before production cutover.
