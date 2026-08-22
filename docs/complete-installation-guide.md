# Complete installation guide

This is the copy-ready installation and operator guide for Favorite CMS 0.1.0. It covers a Windows development/local PC and an Ubuntu VPS. Commands use the existing explicit Configuration, Migration, Installation, Storage, Theme, Plugin, and Tool Worker contracts. Normal application startup never migrates or installs the CMS.

## 1. What runs

| Process | Default bind | Purpose |
| --- | --- | --- |
| FastAPI backend | `127.0.0.1:8020` | API, public `/site/*`, health, Auth and Permission |
| Next.js frontend | `127.0.0.1:3010` | Admin and frontend UI |
| Optional Tool Worker | `127.0.0.1:8060` | Fixed OCR/direct-media operations |

Port 3000 is not used by the supplied Windows launcher. PostgreSQL is required for production. SQLite is suitable only for local development and the documented bounded recovery workflow. The mounted Storage directory, PostgreSQL backups, reverse proxy, TLS, firewall, and process supervision are operator-owned.

## 2. Required software

- Git
- Python 3.12 or newer
- Node.js 22 and Corepack/pnpm
- PostgreSQL for production
- Optional OCR: Tesseract 5 with `eng` and `ben`

Verify before installing:

```text
git --version
python --version
node --version
pnpm --version
```

Do not store passwords or populated environment files in Git. Never prefix a secret with `NEXT_PUBLIC_`.

## 3. Windows local PC

### 3.1 Clone and install

Open PowerShell. Replace the target path only if needed.

```powershell
New-Item -ItemType Directory -Force D:\Server\Shofikul | Out-Null
git clone https://github.com/favoritecode/Favorite-CMS.git D:\Server\Shofikul\web
Set-Location D:\Server\Shofikul\web
git switch main

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check

Set-Location frontend
pnpm install --frozen-lockfile
pnpm run build
Set-Location ..
```

If the repository already exists, do not overwrite it. Check for local work first:

```powershell
Set-Location D:\Server\Shofikul\web
git status
git pull --ff-only origin main
```

### 3.2 Create local configuration

The Windows launcher reads either `D:\Server\Shofikul\web\.env` or the ignored sibling file `D:\Server\Shofikul\web.env`. Prefer the sibling file so runtime configuration is outside the checkout.

```powershell
Copy-Item .env.production.example D:\Server\Shofikul\web.env
notepad D:\Server\Shofikul\web.env
```

Set these keys. The values below are placeholders, not production credentials:

```dotenv
FAVORITE_ENV=development
FAVORITE_DEBUG=false
FAVORITE_HOST=127.0.0.1
FAVORITE_PORT=8020
FAVORITE_DATABASE_URL=sqlite:///D:/Server/Shofikul/web-runtime/favorite-cms.db
FAVORITE_STORAGE_PROVIDER=mounted
FAVORITE_STORAGE_ROOT=D:/Server/Shofikul/web-runtime/storage
FAVORITE_AUTH_JWT_SECRET=REPLACE_WITH_A_LONG_RANDOM_SECRET
FAVORITE_ACTIVE_THEME=favorite.theme.starter
FAVORITE_API_URL=http://127.0.0.1:8020
FAVORITE_TOOL_WORKER_URL=http://127.0.0.1:8060
FAVORITE_TOOL_WORKER_TOKEN=REPLACE_WITH_A_DIFFERENT_RANDOM_SECRET
FAVORITE_WORKER_TOKEN=REPLACE_WITH_THE_SAME_WORKER_SECRET
FAVORITE_WORKER_ALLOWED_HOSTS=favoriteweb.net,www.favoriteweb.net
FAVORITE_WORKER_SPOOL=D:/Server/Shofikul/web-runtime/worker-storage
FAVORITE_WORKER_TESSERACT=tesseract
```

Create the runtime directories and generate independent secrets without printing them into project files:

```powershell
New-Item -ItemType Directory -Force D:\Server\Shofikul\web-runtime\storage | Out-Null
New-Item -ItemType Directory -Force D:\Server\Shofikul\web-runtime\worker-storage | Out-Null
$authSecret = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(48)).ToLower()
$workerSecret = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(48)).ToLower()
```

Paste `$authSecret` into `FAVORITE_AUTH_JWT_SECRET`. Paste `$workerSecret` into both Worker token settings, then clear the variables:

```powershell
Remove-Variable authSecret,workerSecret
```

For PostgreSQL, replace the SQLite URL with a dedicated SQLAlchemy URL. Do not paste it into chat, logs, or source control:

```dotenv
FAVORITE_ENV=production
FAVORITE_DATABASE_URL=postgresql+psycopg://favorite_cms:YOUR_PASSWORD@127.0.0.1:5432/favorite_cms
```

### 3.3 Load configuration and initialize once

The CLI reads process environment. This helper imports the ignored file into only the current PowerShell process:

```powershell
Get-Content D:\Server\Shofikul\web.env | ForEach-Object {
  if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$' -and -not $_.TrimStart().StartsWith('#')) {
    [Environment]::SetEnvironmentVariable($matches[1], $matches[2].Trim('"').Trim("'"), 'Process')
  }
}
```

Check first. Migration and installation are always explicit:

```powershell
.\.venv\Scripts\favorite-cms.exe status
.\.venv\Scripts\favorite-cms.exe migrate
.\.venv\Scripts\favorite-cms.exe status
```

For the first operator, use the protected `site-owner` role. It has a fixed, inspectable 0.1.0 set of explicit PermissionEngine grants; it is not an authorization bypass. The CLI still requires at least one explicit authorization tuple:

```powershell
.\.venv\Scripts\favorite-cms.exe install `
  --email "owner@example.com" `
  --display-name "Site Owner" `
  --role "site-owner" `
  --authorization "admin.diagnostics.view:application.admin.platform:view:admin_diagnostics"
```

The command securely prompts for the initial password. For automation, pipe exactly one password line and add `--password-stdin`; take care that shell history and CI logs cannot expose it. Never reinstall an already installed CMS. Confirm:

```powershell
.\.venv\Scripts\favorite-cms.exe status
```

Expected result: `Installation: installed` and `Pending migrations: 0`.

### 3.4 Start and verify

The existing launcher loads the environment file and starts or safely reuses Worker 8060, backend 8020, and frontend 3010:

```powershell
.\scripts\start-local-cms.ps1
```

Verify without exposing tokens:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/health/live
Invoke-RestMethod http://127.0.0.1:8020/health/ready
Invoke-WebRequest http://127.0.0.1:8020/site/welcome -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:3010/admin/login -UseBasicParsing
```

Open:

- Admin: `http://127.0.0.1:3010/admin/login`
- Public site: `http://127.0.0.1:8020/site/welcome`
- Worker information: `http://127.0.0.1:8060/`

The authenticated Worker health route is `/v1/health`; a request without the bearer token should be denied. A previous `{"detail":"Not Found"}` at Worker `/` means an older Worker process is still running—restart it with the launcher.

### 3.5 Optional Windows sign-in startup

Run an elevated PowerShell once:

```powershell
Set-Location D:\Server\Shofikul\web
.\scripts\install-local-cms-autostart.ps1
```

Remove the scheduled task if no longer wanted:

```powershell
Unregister-ScheduledTask -TaskName "Favorite CMS Local Servers" -Confirm
```

## 4. Ubuntu VPS production installation

The following is a provider-neutral Ubuntu layout. Review commands before running them and use an approved Node.js 22 package source for your Ubuntu release.

### 4.1 OS packages and service account

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip postgresql nginx curl ca-certificates tesseract-ocr tesseract-ocr-eng tesseract-ocr-ben
node --version
sudo corepack enable
corepack prepare pnpm@latest --activate
pnpm --version
sudo useradd --system --create-home --home-dir /var/lib/favorite-cms --shell /usr/sbin/nologin favorite-cms
sudo mkdir -p /opt/favorite-cms /srv/favorite-cms/storage /srv/favorite-cms/worker-storage /etc/favorite-cms
sudo chown -R favorite-cms:favorite-cms /opt/favorite-cms /srv/favorite-cms
```

Install Node.js 22 from the current official Node.js instructions before `corepack` if `node --version` is missing or is not version 22. Do not continue with an unsupported Node version.

### 4.2 Obtain and build source

```bash
sudo -u favorite-cms git clone https://github.com/favoritecode/Favorite-CMS.git /opt/favorite-cms
cd /opt/favorite-cms
sudo -u favorite-cms python3 -m venv .venv
sudo -u favorite-cms .venv/bin/python -m pip install --upgrade pip
sudo -u favorite-cms .venv/bin/python -m pip install .
sudo -u favorite-cms .venv/bin/python -m pip check
cd frontend
sudo -u favorite-cms pnpm install --frozen-lockfile
sudo -u favorite-cms pnpm run build
```

You may extract the verified source distribution ZIP into `/opt/favorite-cms` instead of cloning. Verify its `.sha256` first and never mix files from two releases.

### 4.3 Create PostgreSQL database

Choose a unique strong password at the PostgreSQL prompt:

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE favorite_cms LOGIN PASSWORD 'REPLACE_AT_DEPLOYMENT';
CREATE DATABASE favorite_cms OWNER favorite_cms;
\q
```

Test connectivity without printing the URL or password. Restrict PostgreSQL to the required host/network and include it in the operator backup policy.

### 4.4 Environment files

Create `/etc/favorite-cms/backend.env` with `sudoedit`. Use real generated secrets, exact locations, and the final HTTPS origin:

```dotenv
FAVORITE_ENV=production
FAVORITE_DEBUG=false
FAVORITE_HOST=127.0.0.1
FAVORITE_PORT=8020
FAVORITE_DATABASE_URL=postgresql+psycopg://favorite_cms:REPLACE_URL_ENCODED_PASSWORD@127.0.0.1:5432/favorite_cms
FAVORITE_STORAGE_PROVIDER=mounted
FAVORITE_STORAGE_ROOT=/srv/favorite-cms/storage
FAVORITE_AUTH_JWT_SECRET=REPLACE_WITH_LONG_RANDOM_SECRET
FAVORITE_ACTIVE_THEME=favorite.theme.starter
FAVORITE_API_URL=http://127.0.0.1:8020
FAVORITE_TOOL_WORKER_URL=http://127.0.0.1:8060
FAVORITE_TOOL_WORKER_TOKEN=REPLACE_WITH_INDEPENDENT_WORKER_SECRET
```

Create `/etc/favorite-cms/frontend.env`:

```dotenv
FAVORITE_API_URL=http://127.0.0.1:8020
NODE_ENV=production
```

Create `/etc/favorite-cms/worker.env`:

```dotenv
FAVORITE_WORKER_TOKEN=REPLACE_WITH_THE_BACKEND_WORKER_SECRET
FAVORITE_WORKER_ALLOWED_HOSTS=favoriteweb.net,www.favoriteweb.net
FAVORITE_WORKER_SPOOL=/srv/favorite-cms/worker-storage
FAVORITE_WORKER_TESSERACT=tesseract
FAVORITE_WORKER_MAX_DOWNLOAD_BYTES=26214400
FAVORITE_WORKER_TIMEOUT_SECONDS=20
FAVORITE_WORKER_CONCURRENCY=2
```

Protect all three files:

```bash
sudo chown root:favorite-cms /etc/favorite-cms/*.env
sudo chmod 0640 /etc/favorite-cms/*.env
```

Do not put backend secrets in the frontend file or any `NEXT_PUBLIC_*` value. The Worker allowlist accepts exact source hosts, never `*`.

### 4.5 Explicit migration and first installation

```bash
sudo -u favorite-cms bash -c 'set -a; source /etc/favorite-cms/backend.env; set +a; cd /opt/favorite-cms; .venv/bin/favorite-cms status'
sudo -u favorite-cms bash -c 'set -a; source /etc/favorite-cms/backend.env; set +a; cd /opt/favorite-cms; .venv/bin/favorite-cms migrate'
sudo -u favorite-cms bash -c 'set -a; source /etc/favorite-cms/backend.env; set +a; cd /opt/favorite-cms; .venv/bin/favorite-cms install --email owner@example.com --display-name "Site Owner" --role site-owner --authorization admin.diagnostics.view:application.admin.platform:view:admin_diagnostics'
sudo -u favorite-cms bash -c 'set -a; source /etc/favorite-cms/backend.env; set +a; cd /opt/favorite-cms; .venv/bin/favorite-cms status'
```

The install command prompts without echoing the password. Use the operator's real email and display name. Expected final state is installed with zero pending migrations.

### 4.6 systemd units

Create `/etc/systemd/system/favorite-worker.service`:

```ini
[Unit]
Description=Favorite CMS Tool Worker
After=network.target

[Service]
Type=simple
User=favorite-cms
Group=favorite-cms
WorkingDirectory=/opt/favorite-cms
EnvironmentFile=/etc/favorite-cms/worker.env
ExecStart=/opt/favorite-cms/.venv/bin/uvicorn favorite_worker.app:create_app --factory --host 127.0.0.1 --port 8060
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/favorite-backend.service`:

```ini
[Unit]
Description=Favorite CMS Backend
After=network.target postgresql.service favorite-worker.service

[Service]
Type=simple
User=favorite-cms
Group=favorite-cms
WorkingDirectory=/opt/favorite-cms
EnvironmentFile=/etc/favorite-cms/backend.env
ExecStart=/opt/favorite-cms/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8020
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/favorite-frontend.service`:

```ini
[Unit]
Description=Favorite CMS Frontend
After=network.target favorite-backend.service

[Service]
Type=simple
User=favorite-cms
Group=favorite-cms
WorkingDirectory=/opt/favorite-cms/frontend
EnvironmentFile=/etc/favorite-cms/frontend.env
ExecStart=/usr/bin/pnpm start --hostname 127.0.0.1 --port 3010
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Confirm the actual `pnpm` path with `command -v pnpm` and update `ExecStart` if needed. Then enable and verify:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now favorite-worker favorite-backend favorite-frontend
sudo systemctl status favorite-worker favorite-backend favorite-frontend --no-pager
curl --fail http://127.0.0.1:8020/health/live
curl --fail http://127.0.0.1:8020/health/ready
curl --fail http://127.0.0.1:8020/site/welcome
curl --fail http://127.0.0.1:3010/admin/login
```

### 4.7 Nginx and TLS

Create `/etc/nginx/sites-available/favorite-cms` and replace the domain:

```nginx
server {
    listen 80;
    server_name favoriteweb.net www.favoriteweb.net;
    client_max_body_size 30m;

    location = / { return 302 /site/welcome; }

    location ~ ^/(admin|explore)(/|$) {
        proxy_pass http://127.0.0.1:3010;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /_next/ {
        proxy_pass http://127.0.0.1:3010;
        proxy_set_header Host $host;
    }

    location ~ ^/(site|api|health)(/|$) {
        proxy_pass http://127.0.0.1:8020;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/favorite-cms /etc/nginx/sites-enabled/favorite-cms
sudo nginx -t
sudo systemctl reload nginx
```

Only ports 22, 80, and 443 should normally be public. Keep PostgreSQL, 8060, 8020, and 3010 private. Obtain TLS using the operator's approved certificate process, redirect HTTP to HTTPS, and configure the final public origin in CMS Settings. `Public website origin` creates safe absolute canonical/SEO URLs; it does not configure DNS, bind a server, or make a domain reachable.

## 5. First login and extensions

1. Open `/admin/login` on the frontend origin.
2. Sign in with the explicit first identity.
3. Verify Dashboard and Diagnostics.
4. Create narrower users/roles through Administration; authorization still goes through PermissionEngine.
5. The Starter Theme is active after installation.
6. Bundled Plugins are inactive by default. Review and explicitly approve their capabilities before activation.
7. OCR/direct-media Plugins need the separately running Worker and only their declared permissions.

Uploaded Plugin ZIPs are declarative packages. Favorite CMS does not execute arbitrary uploaded Python/JavaScript and has no marketplace or remote Plugin installer.

## 6. Update, backup, and recovery

Before an update:

```bash
cd /opt/favorite-cms
git status
git fetch origin
git log --oneline HEAD..origin/main
```

Back up PostgreSQL with the operator's native PostgreSQL process and back up `/srv/favorite-cms/storage` and relevant configuration separately. Favorite CMS 0.1.0 does not claim PostgreSQL-native backup/restore. Its documented built-in recovery boundary is SQLite plus mounted Storage. Rehearse restore before production cutover.

For an approved source update: stop services, preserve database/Storage/configuration, update source, install locked dependencies, build frontend, run `favorite-cms migrate` explicitly, then restart and verify. Never run installation again to perform an update.

## 7. Troubleshooting

- **`Installation: uninstalled`**: run migration and explicit first installation; do not invent an identity.
- **Pending migrations above zero**: stop normal deployment and run `favorite-cms migrate` once with the correct environment.
- **`An active Theme is required`**: confirm `FAVORITE_ACTIVE_THEME=favorite.theme.starter`, the Theme files exist, and the backend loaded the intended environment.
- **Backend 503/not ready**: check PostgreSQL, migration state, mounted Storage permissions, Theme state, and redacted service logs.
- **Frontend cannot reach API**: `FAVORITE_API_URL` must be available to the Next.js server and point to the private backend; it is not a browser/public variable.
- **Worker 401/403**: verify matching Worker tokens and declared Plugin permission; do not log the token.
- **Worker root 404**: an older Worker is running. Restart the configured Worker; current 0.1.0 returns service information at `/`.
- **OCR language missing**: `tesseract --list-langs` must include `eng` and `ben`.
- **Port already used**: identify the owning process. Do not kill an unrelated service automatically.

## 8. Production checklist

- PostgreSQL connectivity tested without exposing credentials
- mounted Storage is durable, writable only by the service, and backed up
- long independent Authentication and Worker secrets configured
- `.env` files outside Git with restrictive permissions
- explicit migration completed; pending count zero
- explicit installation completed; no implicit administrator bypass
- backend, frontend, and optional Worker supervised separately
- liveness, readiness, public page, and Admin login return successfully
- only reverse proxy ports exposed publicly
- DNS, TLS, firewall, log retention, monitoring, and process supervision configured by operator
- Plugin capabilities reviewed before activation
- backup and restore rehearsal completed
