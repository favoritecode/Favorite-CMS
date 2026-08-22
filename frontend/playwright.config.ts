import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 90_000,
  // The real-transport suite deliberately shares one CMS installation so its
  // lifecycle workflows must be serialized rather than racing shared state.
  workers: 1,
  use: { baseURL: "http://127.0.0.1:3000" },
  webServer: [
    {
      command: ".venv\\Scripts\\python.exe -m uvicorn backend.tests.e2e_app:app --host 127.0.0.1 --port 8011",
      cwd: "..",
      url: "http://127.0.0.1:8011/health/live",
      reuseExistingServer: false,
      env: {
        FAVORITE_ENV: "test",
        FAVORITE_DATABASE_URL: `sqlite+pysqlite:///storage/e2e-${process.pid}.db`,
        FAVORITE_STORAGE_ROOT: `storage/e2e-files-${process.pid}`,
        FAVORITE_AUTH_JWT_SECRET: "playwright-signing-key-at-least-thirty-two-bytes",
        FAVORITE_ACTIVE_THEME: "favorite.theme.starter",
      },
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      command: "node tests/dev-server.mjs",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      env: { FAVORITE_API_URL: "http://127.0.0.1:8011" },
      stdout: "ignore",
      stderr: "ignore",
    },
  ],
});
