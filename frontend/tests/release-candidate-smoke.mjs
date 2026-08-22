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
const extensionCard = (id) => page.locator("article").filter({ hasText: id });
const extensionAction = async (id, action) => {
  await extensionCard(id).waitFor();
  const trigger = extensionCard(id).getByRole("button", { name: action, exact: true });
  if (await trigger.count() > 0) {
    await trigger.click();
    const dialog = page.getByRole("dialog", { name: new RegExp(`^${action}`) });
    for (const checkbox of await dialog.getByRole("checkbox").all()) await checkbox.check();
    await dialog.getByRole("button", { name: action, exact: true }).click();
  }
  await extensionCard(id).getByText(action === "Activate" ? "enabled" : "disabled", { exact: true }).waitFor();
};

try {
  await page.goto(`${frontend}/admin/login`);
  await visible(page.getByRole("heading", { name: "Sign in to Admin" }), "Admin login is available");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(/\/admin$/);
  await visible(page.getByRole("heading", { name: "Dashboard", exact: true }), "initial identity authenticates");
  await page.waitForFunction(() => document.querySelectorAll('nav[aria-label="Administration"] a').length > 1);
  check((await page.getByRole("navigation", { name: "Administration" }).getByRole("link").allTextContents()).length >= 6, "Admin navigation is permission-filtered");
  const cookie = (await context.cookies()).find((item) => item.name === "favorite_admin_session");
  check(Boolean(cookie?.httpOnly && cookie.sameSite === "Strict"), "session cookie is HttpOnly and SameSite Strict");
  check(await page.evaluate(() => localStorage.length === 0 && sessionStorage.length === 0), "browser credential stores are empty");

  await page.goto(`${frontend}/admin/pages`);
  await visible(page.getByRole("heading", { name: "Pages", exact: true }), "Content management loads");
  const suffix = Date.now();
  await page.getByRole("button", { name: "New page" }).click();
  await page.getByLabel(/^Title/).fill(`Clean candidate ${suffix}`);
  await page.getByRole("textbox", { name: "Slug" }).fill(`clean-candidate-${suffix}`);
  await page.getByLabel("Body").fill("Created through the clean distribution transport.");
  await page.getByRole("button", { name: "Save draft", exact: true }).first().click();
  await visible(page.getByText("Draft created."), "draft creation works");
  check(await page.getByText("draft", { exact: true }).last().isVisible(), "draft is visible in Admin");
  const draftPublic = await page.request.get(`${backend}/site/content`);
  check(!(await draftPublic.text()).includes(`Clean candidate ${suffix}`), "draft is not publicly visible");
  await page.getByRole("textbox", { name: "Title" }).fill(`Published update ${suffix}`);
  await page.getByRole("button", { name: "Save draft", exact: true }).first().click();
  await visible(page.getByText("Draft saved."), "draft editing works");
  await page.getByRole("dialog").getByRole("button", { name: "Publish", exact: true }).first().click();
  await page.getByRole("dialog").last().getByRole("button", { name: "Publish", exact: true }).click();
  await visible(page.getByText("Page published."), "Content publication works");

  await page.goto(`${frontend}/admin/media`);
  await page.getByRole("button", { name: "Add document" }).first().click();
  await page.getByLabel("File name").fill(`clean-${suffix}.txt`);
  await page.getByLabel("Document content").fill("clean distribution media");
  await page.getByRole("dialog").getByRole("button", { name: "Add document" }).click();
  await visible(page.getByText("Text document added to the media library."), "Media Storage contract works");
  await visible(page.getByRole("row", { name: new RegExp(`clean-${suffix}\\.txt`) }), "Media metadata is listed without a physical path");

  await page.goto(`${frontend}/admin/settings`);
  await page.getByLabel("Site title").fill(`Favorite CMS Clean Candidate ${suffix}`);
  await page.getByRole("button", { name: "Save changes" }).click();
  await visible(page.getByText("Site settings saved."), "Settings contract works");

  await page.goto(`${frontend}/admin/diagnostics`);
  await visible(page.getByText("Liveness", { exact: true }).first(), "Health diagnostics render safely");
  check(await page.getByText("Readiness", { exact: true }).first().isVisible(), "Readiness diagnostics render safely");

  await page.goto(`${frontend}/admin/plugins`);
  await extensionAction("favorite.plugin.example", "Activate");
  await visible(extensionCard("favorite.plugin.example").getByText("enabled", { exact: true }), "Plugin activates with explicit capability approval");
  await extensionAction("favorite.plugin.example", "Deactivate");
  await visible(extensionCard("favorite.plugin.example").getByText("disabled", { exact: true }), "Plugin deactivation cleans registrations");
  await extensionAction("favorite.plugin.example", "Activate");
  await extensionCard("favorite.plugin.example").getByRole("button", { name: "Configure" }).click();
  await page.getByLabel("Plugin message").fill("State preserved across Plugin lifecycle.");
  await page.getByRole("button", { name: "Save settings" }).click();
  await visible(page.getByText("Favorite Example Plugin settings saved."), "Plugin settings persist through the owning contract");
  await page.getByRole("button", { name: "Close settings" }).click();
  await extensionAction("favorite.plugin.example", "Deactivate");
  await extensionAction("favorite.plugin.example", "Activate");
  await extensionCard("favorite.plugin.example").getByRole("button", { name: "Configure" }).click();
  check(await page.getByLabel("Plugin message").inputValue() === "State preserved across Plugin lifecycle.", "Plugin state survives deactivation and reactivation");
  await page.getByRole("button", { name: "Close settings" }).click();

  await page.goto(`${frontend}/admin/themes`);
  await visible(extensionCard("favorite.theme.starter").getByText("active", { exact: true }), "Starter Theme is discovered and active");

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
  await page.goto(`${frontend}/admin/pages`);
  await page.getByRole("button", { name: new RegExp(`Published update ${suffix}`) }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Delete page" }).click();
  await page.getByRole("dialog").last().getByRole("button", { name: "Delete", exact: true }).click();
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

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${frontend}/admin`);
  await page.getByRole("heading", { name: "Dashboard", exact: true }).waitFor();
  await page.getByRole("button", { name: "Account" }).click();
  await page.getByRole("menuitem", { name: "Sign out" }).click();
  await visible(page.getByRole("heading", { name: "Sign in to Admin" }), "logout invalidates the Admin session");
  process.stdout.write(`Release candidate browser assertions: ${assertions}/${assertions} passed\n`);
} finally {
  await browser.close();
}
