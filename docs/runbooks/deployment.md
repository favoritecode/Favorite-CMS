# Provider-neutral deployment runbook

1. Verify the release SHA-256, extract into a clean directory, and configure approved production values outside the package.
2. Install Python 3.12+ runtime dependencies from `pyproject.toml` and frontend dependencies with `pnpm install --frozen-lockfile` on Node.js 22.
3. Confirm PostgreSQL connectivity, durable mounted Storage readiness, compatible Plugin/Theme manifests, and a verified provider-owned recovery point when required.
4. Run `favorite-cms migrate`; stop on failure. Normal application startup never applies migrations.
5. Run the explicit `favorite-cms install` command for an uninstalled instance, supplying the initial identity, caller-selected role, and every explicit authorization. Confirm `favorite-cms status` reports `installed` and zero pending migrations.
6. Build the frontend with `pnpm run build`.
7. Start `uvicorn backend.main:app` and `pnpm start`, with server-only `FAVORITE_API_URL` pointing Next.js to FastAPI.
8. Route `/site/*`, APIs, and Health to FastAPI; route `/admin/*`, `/explore/*`, and frontend pages to Next.js. The ingress product is operator-selected.
9. Require `/health/live`, `/health/ready`, public Theme rendering, Admin login, and permission checks before traffic cutover.
10. Operator acceptance: open `<frontend>/admin/login`, verify authorized navigation, then open `<backend>/site/welcome`. Confirm bundled Plugins are inactive unless explicitly approved and activated.
11. Record the release result. Do not claim rollback across irreversible migrations.

Hosting, process manager, proxy, TLS terminator, Storage, Queue, and alerting providers remain deployment choices.
