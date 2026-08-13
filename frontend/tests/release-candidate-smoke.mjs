import { chromium } from "@playwright/test";

const frontend = process.env.FAVORITE_SMOKE_FRONTEND_URL ?? "http://127.0.0.1:3031";
const backend = process.env.FAVORITE_SMOKE_BACKEND_URL ?? "http://127.0.0.1:8031";
const email = process.env.FAVORITE_SMOKE_EMAIL ?? "phase18-operator@example.invalid";
const password = process.env.FAVORITE_SMOKE_PASSWORD;
if (!password) throw new Error("FAVORITE_SMOKE_PASSWORD is required");

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();
let assertions = 0;
const check = (condition, label) => {
  if (!condition) throw new Error(`Release smoke failed: ${label}`);
  assertions += 1;
  process.stdout.write(`ok ${assertions} - ${label}\n`);
};
const visible = async (locator, label) => {
  await locator.waitFor({ state: "visible" });
  check(true, label);
};

try {
  await page.goto(`${frontend}/admin`);
  await visible(page.getByRole("heading", { name: "Admin sign in" }), "unauthenticated Admin is denied");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(/\/admin$/);
  await visible(page.getByRole("heading", { name: "Admin dashboard" }), "initial identity authenticates");
  await page.waitForFunction(() => document.querySelectorAll('nav[aria-label="Administration"] a').length > 1);
  check((await page.getByRole("navigation", { name: "Administration" }).getByRole("link").allTextContents()).length >= 6, "Admin navigation is permission-filtered");
  const cookie = (await context.cookies()).find((item) => item.name === "favorite_admin_session");
  check(Boolean(cookie?.httpOnly && cookie.sameSite === "Strict"), "session cookie is HttpOnly and SameSite Strict");
  check(await page.evaluate(() => localStorage.length === 0 && sessionStorage.length === 0), "browser credential stores are empty");

  await page.goto(`${frontend}/admin/manage`);
  await visible(page.getByRole("heading", { name: "CMS management" }), "dashboard management surface loads");
  const suffix = Date.now();
  await page.getByLabel(/^Title/).fill(`Clean candidate ${suffix}`);
  await page.getByLabel("Slug").fill(`clean-candidate-${suffix}`);
  await page.getByLabel("Body").fill("Created through the clean distribution transport.");
  await page.getByRole("button", { name: "Create draft" }).click();
  await page.getByRole("button", { name: new RegExp(`Clean candidate ${suffix}`) }).click();
  check(await page.getByText("draft", { exact: true }).last().isVisible(), "draft is visible in Admin");
  const draftPublic = await page.request.get(`${backend}/site/content`);
  check(!(await draftPublic.text()).includes(`Clean candidate ${suffix}`), "draft is not publicly visible");
  await page.getByLabel("Edit title").fill(`Edited clean candidate ${suffix}`);
  await page.getByLabel("Edit body").fill("Edited before publication through the clean distribution transport.");
  await page.getByRole("button", { name: "Save changes" }).click();
  await page.getByRole("status").filter({ hasText: "Draft changes saved" }).waitFor();
  check(true, "draft edit works");
  await page.getByRole("button", { name: "Publish publicly", exact: true }).click();
  await page.getByRole("status").filter({ hasText: "published" }).waitFor();
  check(true, "Content create and publish works");
  await page.getByLabel("Edit title").fill(`Published update ${suffix}`);
  await page.getByLabel("Edit body").fill("Updated after publication through the owning Content contract.");
  await page.getByRole("button", { name: "Save changes" }).click();
  await page.getByRole("status").filter({ hasText: "Draft changes saved" }).waitFor();
  check(true, "published Content edit works");
  await page.getByLabel("File name").fill(`clean-${suffix}.txt`);
  await page.getByLabel(/^Text document content/).fill("clean distribution media");
  await page.getByRole("button", { name: "Store media" }).click();
  await page.getByRole("status").filter({ hasText: "Media stored" }).waitFor();
  check(true, "Media Storage contract works");
  await page.getByLabel("File name").fill(`clean-${suffix}.txt`);
  await page.getByLabel(/^Text document content/).fill("duplicate should fail");
  await page.getByRole("button", { name: "Store media" }).click();
  await page.getByRole("status").filter({ hasText: "Media stored" }).waitFor();
  check(true, "duplicate Media name receives a distinct Media identity");
  await page.getByLabel("Site title", { exact: true }).fill("Favorite CMS Clean Candidate");
  await page.getByRole("button", { name: "Save setting" }).click();
  await page.getByRole("status").filter({ hasText: "Setting saved" }).waitFor();
  check(true, "Settings contract works");
  check(await page.getByText("Liveness", { exact: true }).isVisible() && await page.getByText("Readiness", { exact: true }).isVisible(), "Health diagnostics render safely");
  await page.getByLabel("I reviewed and approve the listed Plugin capabilities").check();
  await page.getByRole("button", { name: "Activate favorite.plugin.example" }).click();
  await page.getByRole("status").filter({ hasText: "activated" }).waitFor();
  check(true, "Plugin activates with explicit capability approval");
  await page.getByRole("button", { name: "Deactivate favorite.plugin.example" }).click();
  await page.getByRole("status").filter({ hasText: "deactivated" }).waitFor();
  check(true, "Plugin deactivation cleans registrations");
  await page.getByRole("button", { name: "Activate favorite.plugin.example" }).click();
  await page.getByRole("status").filter({ hasText: "favorite.plugin.example activated" }).waitFor();
  await page.getByLabel("Plugin message").fill("State preserved across Plugin lifecycle.");
  await page.getByRole("button", { name: "Save Plugin state" }).click();
  await page.getByRole("status").filter({ hasText: "Plugin state saved" }).waitFor();
  await page.getByRole("button", { name: "Deactivate favorite.plugin.example" }).click();
  await page.getByRole("status").filter({ hasText: "favorite.plugin.example deactivated" }).waitFor();
  await page.getByRole("button", { name: "Activate favorite.plugin.example" }).click();
  await page.getByRole("status").filter({ hasText: "favorite.plugin.example activated" }).waitFor();
  check(await page.getByLabel("Plugin message").inputValue() === "State preserved across Plugin lifecycle.", "Plugin state survives deactivation and reactivation");
  for (const plugin of ["favorite.plugin.seo", "favorite.plugin.contact", "favorite.plugin.sitemap", "favorite.plugin.analytics"]) {
    await page.getByRole("button", { name: `Activate ${plugin}` }).click();
    await page.getByRole("status").filter({ hasText: `${plugin} activated` }).waitFor();
  }
  check(await page.getByRole("heading", { name: "SEO", exact: true }).isVisible(), "all bundled first-party Plugins activate through capability approval");
  check(await page.getByText("favorite.theme.starter", { exact: false }).first().isVisible(), "Starter Theme is discovered and active");

  await page.goto(`${frontend}/explore`);
  await page.getByLabel("Query").fill("published update");
  await page.getByRole("button", { name: "Run" }).click();
  await page.getByLabel("Result").filter({ hasText: `Published update ${suffix}` }).waitFor();
  check(true, "Search returns published Content");
  await page.getByLabel("Workflow").selectOption("localization");
  await page.getByRole("button", { name: "Run" }).click();
  await page.getByLabel("Result").filter({ hasText: '"fallback":true' }).waitFor();
  check(true, "Localization fallback works");

  await page.goto(`${backend}/site/welcome`);
  await visible(page.getByRole("heading", { level: 1 }), "public Routing Rendering and Theme flow works");
  check(await page.locator('meta[name="favorite-renderer"]').getAttribute("content") === "backend", "public response identifies backend Rendering");
  await page.goto(`${backend}/site/content`);
  await page.getByRole("link", { name: `Published update ${suffix}` }).first().click();
  await visible(page.getByRole("heading", { name: `Published update ${suffix}` }), "public Content detail renders updated published output");
  await page.goto(`${frontend}/admin/manage`);
  await page.getByRole("button", { name: new RegExp(`Published update ${suffix}`) }).click();
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "Delete" }).click();
  await page.getByRole("button", { name: new RegExp(`Published update ${suffix}`) }).waitFor({ state: "detached" });
  const deletedListing = await page.request.get(`${backend}/site/content`);
  check(!(await deletedListing.text()).includes(`Published update ${suffix}`), "deleted Content disappears publicly");
  await page.goto(`${backend}/site/missing-phase18-resource`);
  const missing = (await page.locator("body").innerText()).toLowerCase();
  check(!/traceback|sqlalchemy|storage\\|server\\/.test(missing), "missing resource response is controlled");
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto(`${backend}/site/welcome`);
  check(await page.getByRole("navigation", { name: "Primary navigation" }).isVisible(), "tablet presentation retains accessible navigation");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${backend}/site/welcome`);
  await page.getByRole("button", { name: "Menu" }).click();
  check(await page.getByRole("navigation", { name: "Primary navigation" }).isVisible(), "mobile navigation works");

  await page.goto(`${frontend}/admin`);
  await page.getByRole("button", { name: "Sign out" }).click();
  await visible(page.getByRole("heading", { name: "Admin sign in" }), "logout invalidates the Admin session");
  process.stdout.write(`Release candidate browser assertions: ${assertions}/${assertions} passed\n`);
} finally {
  await browser.close();
}
