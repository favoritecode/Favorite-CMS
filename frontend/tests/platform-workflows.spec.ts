import { expect, test, type Page } from "@playwright/test";

const password = "correct horse battery staple";
async function login(page: Page) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill("operator@example.test");
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);
}
function extensionCard(page: Page, id: string) {
  return page.locator("article").filter({ hasText: id });
}
async function extensionAction(page: Page, id: string, action: "Activate" | "Deactivate") {
  await extensionCard(page, id).getByRole("button", { name: action, exact: true }).click();
  const dialog = page.getByRole("dialog", { name: new RegExp(`^${action}`) });
  if (action === "Activate") {
    for (const checkbox of await dialog.getByRole("checkbox").all()) await checkbox.check();
  }
  await dialog.getByRole("button", { name: action, exact: true }).click();
  await expect(extensionCard(page, id)).toContainText(action === "Activate" ? "enabled" : "disabled");
}
async function configurePlugin(page: Page, id: string) {
  await extensionCard(page, id).getByRole("button", { name: "Configure" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
}
async function savePluginSettings(page: Page) {
  const [response] = await Promise.all([
    page.waitForResponse(response => response.url().includes("/admin/manage/transport/plugin-") && response.request().method() === "PATCH"),
    page.getByRole("button", { name: "Save settings" }).click(),
  ]);
  expect(response.status(), await response.text()).toBe(200);
}

test("content, media, settings, diagnostics, and extension workflows use the real platform", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Dashboard", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "System health" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Active theme" })).toBeVisible();
  await page.goto("/admin/pages");
  await expect(page.getByRole("heading", { name: "Pages", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "New page" }).click();
  await expect(page.getByText("Welcome to Favorite CMS").first()).toBeVisible();
  const suffix = Date.now();
  await page.getByLabel(/^Title/).fill(`Browser-created page ${suffix}`);
  await page.getByRole("textbox", { name: "Slug" }).fill(`browser-${suffix}`);
  await page.getByLabel("Body").fill("Created through UI, HTTP, API, Permission, and Content Engine.");
  await page.getByLabel("Upload from PC/mobile").setInputFiles({
    name: "browser-cover.png", mimeType: "image/png",
    buffer: Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.from("browser-image")]),
  });
  await expect(page.getByText("Featured image uploaded and attached.")).toBeVisible();
  await expect(page.getByText("Draft saved automatically.").first()).toBeVisible();
  await page.getByRole("textbox", { name: "Title", exact: true }).fill(`Browser-edited page ${suffix}`);
  await expect(page.getByText("Draft saved automatically.").first()).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Publish now", exact: true }).first().click();
  await expect(page.getByText("Page published.")).toBeVisible();
  await expect(page.getByText("published", { exact: true }).last()).toBeVisible();
  await page.goto("/admin/media");
  await page.getByRole("button", { name: "Add media" }).first().click();
  await page.getByLabel("File").setInputFiles({ name: "browser-note.txt", mimeType: "text/plain", buffer: Buffer.from("stored through Media and Storage") });
  await page.getByRole("dialog").getByRole("button", { name: "Upload media" }).click();
  await expect(page.getByText("Media uploaded successfully.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "browser-note.txt" })).toBeVisible();
  await page.goto("/admin/settings");
  await page.getByLabel("Site title").fill("Favorite Browser CMS");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText("Site settings saved.")).toBeVisible();
  await page.goto("/admin/diagnostics");
  await expect(page.getByText("Liveness")).toBeVisible();
  await expect(page.getByText("Readiness", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Configuration", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Operator-controlled lifecycle" })).toBeVisible();
  await expect(page.getByText("explicit", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Services", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Content and presentation" })).toBeVisible();
  await page.goto("/admin/plugins");
  await extensionAction(page, "tests.plugin.healthy", "Activate");
  await extensionAction(page, "tests.plugin.healthy", "Deactivate");
  await extensionCard(page, "tests.plugin.failing").getByRole("button", { name: "Activate", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Activate", exact: true }).click();
  await expect(page.getByText(/failed safely|validation/i)).toBeVisible();
  await page.goto("/admin/themes");
  await extensionCard(page, "tests.theme.failing").getByRole("button", { name: "Activate", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Activate", exact: true }).click();
  await expect(page.getByText(/failed safely|validation/i)).toBeVisible();
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
  await page.goto("/admin/plugins");
  await expect(extensionCard(page, "favorite.plugin.example")).toBeVisible();
  await extensionAction(page, "favorite.plugin.example", "Activate");
  await configurePlugin(page, "favorite.plugin.example");
  await page.getByLabel("Plugin message").fill("Saved through the real Plugin API.");
  await savePluginSettings(page);
  await page.getByRole("button", { name: "Close settings" }).click();
  await page.goto("/admin/settings");
  await expect(page.getByRole("heading", { name: "Active Plugin settings" })).toBeVisible();
  await expect(page.getByText("Example Plugin", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Configure" }).click();
  await expect(page.getByLabel("Plugin message")).toHaveValue("Saved through the real Plugin API.");
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
  await page.goto("/admin/plugins");
  await extensionAction(page, "favorite.plugin.example", "Deactivate");
  const removed = await page.request.get("http://127.0.0.1:8011/plugins/example");
  expect(removed.status()).toBe(404);
  await extensionAction(page, "favorite.plugin.example", "Activate");
  await configurePlugin(page, "favorite.plugin.example");
  await expect(page.getByLabel("Plugin message")).toHaveValue("Saved through the real Plugin API.");
  const homepage = await page.request.get("http://127.0.0.1:8011/site/welcome");
  expect(homepage.status()).toBe(200);
  expect(await homepage.text()).toContain("Favorite Starter");
});

test("first-party Plugin suite uses real Admin, API, Routing, and Rendering contracts", async ({ page }) => {
  await login(page); await page.goto("/admin/pages");
  await expect(page.getByRole("heading", { name: "Pages", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "New page" }).click();
  await page.getByLabel(/^Title/).fill("Phase 22 SEO content");
  await page.getByRole("textbox", { name: "Slug" }).fill("phase-22-seo-content");
  await page.getByLabel("Body").fill("Content-owned SEO projection body.");
  await expect(page.getByText("Draft saved automatically.").first()).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Publish now", exact: true }).first().click();
  await page.goto("/admin/plugins");
  for (const plugin of ["favorite.plugin.seo", "favorite.plugin.contact", "favorite.plugin.sitemap", "favorite.plugin.analytics"]) {
    await extensionAction(page, plugin, "Activate");
  }
  await configurePlugin(page, "favorite.plugin.seo");
  await page.getByLabel("SEO site title").fill("Favorite Suite Site");
  await page.getByLabel("Meta description").fill("Metadata configured by the SEO Plugin.");
  await page.getByLabel("Canonical public origin").fill("https://example.test");
  await savePluginSettings(page);
  await page.getByRole("button", { name: "Close settings" }).click();
  await expect(extensionCard(page, "favorite.plugin.seo")).toContainText("content.read");
  await page.goto("/admin/pages");
  await page.getByRole("button", { name: /Phase 22 SEO content/ }).click();
  await page.getByLabel("SEO title").fill("Search-ready Phase 22 title");
  await page.getByLabel("Meta description").fill("Projected & safely escaped.");
  await page.getByLabel("Open Graph title").fill('Projected "title"');
  await page.getByRole("button", { name: "Save SEO metadata" }).click();
  await expect(page.getByText("Content SEO metadata saved.")).toBeVisible();
  await page.getByLabel("Body").fill("Content edited after SEO metadata was saved.");
  await page.getByRole("dialog").getByRole("button", { name: "Save changes" }).first().click();
  await expect(page.getByText("Draft saved.")).toBeVisible();
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
  expect(projectedHtml).toContain("<title>Search-ready Phase 22 title</title>");
  expect(projectedHtml).toContain('content="Projected &quot;title&quot;"');

  await page.goto("/admin/plugins");
  await configurePlugin(page, "favorite.plugin.contact");
  await page.getByLabel("Contact recipient").fill("site-owner@example.test");
  await savePluginSettings(page);
  await page.goto("http://127.0.0.1:8011/contact");
  await page.getByRole("button", { name: "Send message" }).click();
  expect(await page.getByLabel("Name").evaluate((input: HTMLInputElement) => input.validationMessage.length > 0)).toBeTruthy();
  await page.getByLabel("Name").fill("Browser Visitor"); await page.getByLabel("Email").fill("visitor@example.test");
  await page.getByLabel("Message").fill("Submitted through the real Plugin API."); await page.getByRole("button", { name: "Send message" }).click();
  await expect(page.getByRole("status")).toHaveText("Your message is pending delivery.");

  await page.goto("/admin/plugins");
  await configurePlugin(page, "favorite.plugin.contact");
  await expect(page.getByText("Pending").locator("..").getByText("1")).toBeVisible();
  await page.getByRole("button", { name: "Close settings" }).click();
  await configurePlugin(page, "favorite.plugin.sitemap");
  await page.getByLabel("Public base URL").fill("https://example.test");
  await savePluginSettings(page);
  await page.getByRole("button", { name: "Close settings" }).click();
  const sitemap = await page.request.get("http://127.0.0.1:8011/sitemap.xml");
  expect(sitemap.status()).toBe(200); expect(sitemap.headers()["content-type"]).toContain("application/xml");
  expect(await sitemap.text()).toContain("https://example.test/site/content/");

  await configurePlugin(page, "favorite.plugin.analytics");
  await page.getByLabel("Analytics provider").selectOption("none"); await page.getByLabel("Analytics site ID").fill("");
  await savePluginSettings(page);
  const disabled = await page.request.get("http://127.0.0.1:8011/site/welcome"); expect(await disabled.text()).not.toContain("favorite-analytics");
  await page.getByLabel("Analytics provider").selectOption("first-party"); await page.getByLabel("Analytics site ID").fill("browser_site");
  await savePluginSettings(page);
  await page.getByRole("button", { name: "Close settings" }).click();
  const enabled = await page.request.get("http://127.0.0.1:8011/site/welcome");
  expect(await enabled.text()).toContain('name="favorite-analytics" content="first-party" data-site-id="browser_site"');

  for (const plugin of ["favorite.plugin.analytics", "favorite.plugin.sitemap", "favorite.plugin.contact", "favorite.plugin.seo"]) {
    await extensionAction(page, plugin, "Deactivate");
  }
  expect((await page.request.get("http://127.0.0.1:8011/contact")).status()).toBe(404);
  expect((await page.request.get("http://127.0.0.1:8011/sitemap.xml")).status()).toBe(404);
  const homepage = await page.request.get("http://127.0.0.1:8011/site/welcome");
  expect(homepage.status()).toBe(200); expect(await homepage.text()).toContain("Favorite Starter");
});
