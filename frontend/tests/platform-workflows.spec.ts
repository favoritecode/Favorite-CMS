import { expect, test, type Page } from "@playwright/test";

const password = "correct horse battery staple";
async function login(page: Page) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill("operator@example.test");
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);
}

test("content, media, settings, diagnostics, and extension workflows use the real platform", async ({ page }) => {
  await login(page);
  await expect(page.getByText("Welcome to Favorite CMS")).toBeVisible();
  await expect(page.getByText("Readiness", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "System status" })).toBeVisible();
  await expect(page.getByText("0 pending")).toBeVisible();
  await page.goto("/admin/manage");
  await expect(page.getByRole("heading", { name: "CMS management" })).toBeVisible();
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  await expect(page.getByText("Welcome to Favorite CMS").first()).toBeVisible();
  const suffix = Date.now();
  await page.getByLabel(/^Title/).fill(`Browser-created page ${suffix}`);
  await page.getByLabel("Slug").fill(`browser-${suffix}`);
  await page.getByLabel("Body").fill("Created through UI, HTTP, API, Permission, and Content Engine.");
  await page.getByRole("button", { name: "Create draft" }).click();
  await expect(page.getByText("Content created as a draft")).toBeVisible();
  await page.getByRole("button", { name: new RegExp(`Browser-created page ${suffix}`) }).click();
  await page.getByLabel("Edit title").fill(`Browser-edited page ${suffix}`);
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("status")).toContainText("Draft changes saved");
  await page.getByRole("button", { name: "Publish publicly", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Content published");
  await expect(page.getByText("published", { exact: true }).last()).toBeVisible();
  await page.getByLabel("File name").fill("browser-note.txt");
  await page.getByLabel(/^Text document content/).fill("stored through Media and Storage");
  await page.getByRole("button", { name: "Store media" }).click();
  await expect(page.getByText("Media stored: browser-note.txt")).toBeVisible();
  await expect(page.getByText(/text\/plain · \d+ bytes/).first()).toBeVisible();
  await page.getByLabel("Site title").fill("Favorite Browser CMS");
  await page.getByRole("button", { name: "Save setting" }).click();
  await expect(page.getByText("Setting saved: Favorite Browser CMS")).toBeVisible();
  await expect(page.getByText("Liveness")).toBeVisible();
  await expect(page.getByText("Readiness", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Configuration readiness" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Operator-controlled lifecycle" })).toBeVisible();
  await expect(page.getByText("Normal startup performs neither migration nor installation.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dependency status" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Service boundaries" })).toBeVisible();
  await page.getByRole("button", { name: "Activate tests.plugin.healthy" }).click();
  await expect(page.getByText("tests.plugin.healthy activated")).toBeVisible();
  await page.getByRole("button", { name: "Deactivate tests.plugin.healthy" }).click();
  await expect(page.getByText("tests.plugin.healthy deactivated")).toBeVisible();
  await page.getByRole("button", { name: "Activate tests.plugin.failing" }).click();
  await expect(page.getByRole("status")).toContainText(/failed safely|validation/i);
  await expect(page.getByRole("heading", { name: "CMS management" })).toBeVisible();
  await page.getByRole("button", { name: "Activate tests.theme.failing" }).click();
  await expect(page.getByRole("status")).toContainText(/failed safely|validation/i);
  const publicPage = await page.request.get("http://127.0.0.1:8011/site/welcome");
  expect(publicPage.status()).toBe(200);
  expect(await publicPage.text()).toContain("Welcome to Favorite CMS");
});

test("public Routing and Rendering return themed HTML and safe missing-resource errors", async ({ page }) => {
  await page.goto("http://127.0.0.1:8011/site/welcome");
  await expect(page.getByRole("heading", { name: "Welcome to Favorite CMS", level: 1 })).toBeVisible();
  await expect(page.locator('meta[name="favorite-renderer"]')).toHaveAttribute("content", "backend");
  await expect(page.locator('meta[name="theme"]')).toHaveAttribute("content", "favorite.theme.starter");
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Explore published content" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Latest published content" })).toBeVisible();
  await expect(page.locator("footer")).toContainText("flexible, neutral foundation");
  expect((await page.locator("body").innerText()).trim().length).toBeGreaterThan(180);

  await page.getByRole("link", { name: "View all content" }).click();
  await expect(page).toHaveURL(/\/site\/content$/);
  await expect(page.getByRole("heading", { name: "Published content", level: 1 })).toBeVisible();
  await page.getByRole("link", { name: "Welcome to Favorite CMS" }).first().click();
  await expect(page.getByRole("heading", { name: "Welcome to Favorite CMS", level: 1 })).toBeVisible();
  await expect(page.getByText("Rendered by the backend presentation pipeline.")).toBeVisible();
  await page.getByRole("link", { name: /Back to published content/ }).click();

  await page.goto("http://127.0.0.1:8011/site/search/backend%20presentation");
  await expect(page.getByRole("heading", { name: "Find published content" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Welcome to Favorite CMS/ })).toBeVisible();
  await page.getByLabel("Search this site").fill("nothing can match this phrase");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.getByText("No matching content found.")).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:8011/site/welcome");
  const navigation = page.getByRole("navigation", { name: "Primary navigation" });
  await expect(navigation).toBeHidden();
  await page.getByRole("button", { name: "Menu" }).click();
  await expect(navigation).toBeVisible();

  await page.goto("http://127.0.0.1:8011/site/does-not-exist");
  expect((await page.locator("body").innerText()).toLowerCase()).not.toMatch(/traceback|storage\\|server\\|sqlalchemy/);
  expect(page.url()).toContain("does-not-exist");
});

test("search and localization render deterministic real backend results", async ({ page }) => {
  await page.goto("/explore");
  await page.getByLabel("Query").fill("backend presentation");
  await page.getByRole("button", { name: "Run" }).click();
  await expect(page.getByLabel("Result")).toContainText("Welcome to Favorite CMS");
  await page.getByLabel("Query").fill("no such indexed resource");
  await page.getByRole("button", { name: "Run" }).click();
  await expect(page.getByLabel("Result")).toHaveText("[]");
  await page.getByLabel("Workflow").selectOption("localization");
  await page.getByRole("button", { name: "Run" }).click();
  await expect(page.getByLabel("Result")).toContainText('"value":"Welcome"');
  await expect(page.getByLabel("Result")).toContainText('"fallback":true');
  await page.getByLabel("Translation key").fill("public.missing");
  await page.getByRole("button", { name: "Run" }).click();
  await expect(page.getByLabel("Result")).toContainText('"missing":true');
});

test("first-party Plugin activates with explicit capabilities and cleans up through real transport", async ({ page }) => {
  await login(page);
  await page.goto("/admin/manage");
  await expect(page.getByText(/favorite\.plugin\.example · v1\.0\.0/)).toBeVisible();
  await page.getByRole("button", { name: "Activate favorite.plugin.example" }).click();
  await expect(page.getByRole("status")).toContainText("Review and approve");
  await page.getByLabel("I reviewed and approve the listed Plugin capabilities").check();
  await page.getByRole("button", { name: "Activate favorite.plugin.example" }).click();
  await expect(page.getByRole("status")).toContainText("favorite.plugin.example activated");
  await expect(page.getByRole("heading", { name: "Example Plugin" })).toBeVisible();
  await page.getByLabel("Plugin message").fill("Saved through the real Plugin API.");
  await page.getByRole("button", { name: "Save Plugin state" }).click();
  await expect(page.getByRole("status")).toContainText("Example Plugin state saved");
  await page.goto("http://127.0.0.1:8011/plugins/example");
  await expect(page.getByRole("heading", { name: "Example Plugin" })).toBeVisible();
  await expect(page.getByText("Saved through the real Plugin API.")).toBeVisible();
  await expect(page.locator('meta[name="plugin"]')).toHaveAttribute("content", "favorite.plugin.example");
  await page.request.delete("/admin/session");
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill("viewer@example.test");
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);
  const forbidden = await page.request.get("/admin/manage/transport/plugin-example");
  expect(forbidden.status()).toBe(403);
  await page.request.delete("/admin/session");
  await login(page);
  await page.goto("/admin/manage");
  await page.getByRole("button", { name: "Deactivate favorite.plugin.example" }).click();
  await expect(page.getByRole("status")).toContainText("favorite.plugin.example deactivated");
  await expect(page.getByRole("heading", { name: "Example Plugin" })).toHaveCount(0);
  const removed = await page.request.get("http://127.0.0.1:8011/plugins/example");
  expect(removed.status()).toBe(404);
  await page.getByLabel("I reviewed and approve the listed Plugin capabilities").check();
  await page.getByRole("button", { name: "Activate favorite.plugin.example" }).click();
  await expect(page.getByLabel("Plugin message")).toHaveValue("Saved through the real Plugin API.");
  const homepage = await page.request.get("http://127.0.0.1:8011/site/welcome");
  expect(homepage.status()).toBe(200);
  expect(await homepage.text()).toContain("Favorite Starter");
});

test("first-party Plugin suite uses real Admin, API, Routing, and Rendering contracts", async ({ page }) => {
  await login(page); await page.goto("/admin/manage");
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  await page.getByLabel(/^Title/).fill("Phase 22 SEO content");
  await page.getByLabel("Slug").fill("phase-22-seo-content");
  await page.getByLabel("Body").fill("Content-owned SEO projection body.");
  await page.getByRole("button", { name: "Create draft" }).click();
  await page.getByRole("button", { name: /Phase 22 SEO content/ }).click();
  await page.getByRole("button", { name: "Publish publicly", exact: true }).click();
  await page.getByLabel("I reviewed and approve the listed Plugin capabilities").check();
  for (const plugin of ["favorite.plugin.seo", "favorite.plugin.contact", "favorite.plugin.sitemap", "favorite.plugin.analytics"]) {
    await page.getByRole("button", { name: `Activate ${plugin}` }).click();
    await expect(page.getByRole("status")).toContainText(`${plugin} activated`);
  }
  await page.getByLabel("SEO site title").fill("Favorite Suite Site");
  await page.getByLabel("Meta description").fill("Metadata configured by the SEO Plugin.");
  await page.getByLabel("Canonical public origin").fill("https://example.test");
  await page.getByRole("button", { name: "Save SEO" }).click();
  await expect(page.getByRole("status")).toContainText("SEO configuration saved");
  await expect(page.getByText(/Required:.*content\.read/).first()).toBeVisible();
  await expect(page.getByText(/Granted:.*content\.read/).first()).toBeVisible();
  await page.getByLabel("Content SEO description").fill("Projected & safely escaped.");
  await page.getByLabel("Open Graph title").fill('Projected "title"');
  await page.getByRole("button", { name: "Save Content SEO" }).click();
  await expect(page.getByRole("status")).toContainText("Content SEO metadata saved");
  await page.getByLabel("Edit body").fill("Content edited after SEO metadata was saved.");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByRole("status")).toContainText("Draft changes saved");
  const seoPage = await page.request.get("http://127.0.0.1:8011/site/welcome"); const seoHtml = await seoPage.text();
  expect(seoHtml).toContain('name="description" content="Metadata configured by the SEO Plugin."');
  expect(seoHtml).toContain('rel="canonical" href="https://example.test/site/welcome"');
  const contentLinks = await page.request.get("http://127.0.0.1:8011/site/content");
  const listingHtml = await contentLinks.text();
  const match = listingHtml.match(/\/site\/content\/([0-9a-f-]{36})[^>]*>Phase 22 SEO content/);
  expect(match).toBeTruthy();
  const projected = await page.request.get(`http://127.0.0.1:8011/site/content/${match![1]}`);
  const projectedHtml = await projected.text();
  expect(projectedHtml).toContain('content="Projected &amp; safely escaped."');
  expect(projectedHtml).toContain('content="Projected &quot;title&quot;"');

  await page.getByLabel("Contact recipient").fill("site-owner@example.test");
  await page.getByRole("button", { name: "Save Contact" }).click();
  await expect(page.getByRole("status")).toContainText("Contact configuration saved");
  await page.goto("http://127.0.0.1:8011/contact");
  await page.getByRole("button", { name: "Send message" }).click();
  expect(await page.getByLabel("Name").evaluate((input: HTMLInputElement) => input.validationMessage.length > 0)).toBeTruthy();
  await page.getByLabel("Name").fill("Browser Visitor"); await page.getByLabel("Email").fill("visitor@example.test");
  await page.getByLabel("Message").fill("Submitted through the real Plugin API."); await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.getByRole("status")).toHaveText("Your message is pending delivery.");

  await page.goto("/admin/manage");
  await expect(page.getByText("Ready", { exact: true })).toBeVisible();
  await expect(page.getByText("Pending").locator("..").getByText("1")).toBeVisible();
  await expect(page.getByText(/Provider: not configured/)).toBeVisible();
  await page.getByLabel("Public base URL").fill("https://example.test");
  await page.getByRole("button", { name: "Save Sitemap" }).click(); await expect(page.getByRole("status")).toContainText("Sitemap configuration saved");
  const sitemap = await page.request.get("http://127.0.0.1:8011/sitemap.xml");
  expect(sitemap.status()).toBe(200); expect(sitemap.headers()["content-type"]).toContain("application/xml");
  expect(await sitemap.text()).toContain("https://example.test/site/content/");

  await page.getByLabel("Analytics provider").selectOption("none"); await page.getByLabel("Analytics site ID").fill("");
  await page.getByRole("button", { name: "Save Analytics" }).click(); await expect(page.getByRole("status")).toContainText("Analytics configuration saved");
  const disabled = await page.request.get("http://127.0.0.1:8011/site/welcome"); expect(await disabled.text()).not.toContain("favorite-analytics");
  await page.getByLabel("Analytics provider").selectOption("first-party"); await page.getByLabel("Analytics site ID").fill("browser_site");
  await page.getByRole("button", { name: "Save SEO" }).click(); await expect(page.getByRole("status")).toContainText("SEO configuration saved");
  await page.getByRole("button", { name: "Save Analytics" }).click();
  await expect(page.getByRole("status")).toContainText("Analytics configuration saved");
  const enabled = await page.request.get("http://127.0.0.1:8011/site/welcome");
  expect(await enabled.text()).toContain('name="favorite-analytics" content="first-party" data-site-id="browser_site"');

  for (const plugin of ["favorite.plugin.analytics", "favorite.plugin.sitemap", "favorite.plugin.contact", "favorite.plugin.seo"]) {
    await page.getByRole("button", { name: `Deactivate ${plugin}` }).click();
    await expect(page.getByRole("status")).toContainText(`${plugin} deactivated`);
  }
  expect((await page.request.get("http://127.0.0.1:8011/contact")).status()).toBe(404);
  expect((await page.request.get("http://127.0.0.1:8011/sitemap.xml")).status()).toBe(404);
  const homepage = await page.request.get("http://127.0.0.1:8011/site/welcome");
  expect(homepage.status()).toBe(200); expect(await homepage.text()).toContain("Favorite Starter");
});
