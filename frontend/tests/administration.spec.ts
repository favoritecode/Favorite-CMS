import { expect, test } from "@playwright/test";

const password = "correct horse battery staple";

async function login(page: import("@playwright/test").Page, email = "operator@example.test", value = password) {
  await page.goto("/admin/login");
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel("Password").fill(value);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);
}

test("authorized operator manages an explicit custom role and user through real APIs", async ({ page }) => {
  await login(page);
  await page.goto("/admin/roles");
  await expect(page.getByRole("heading", { name: "Roles & permissions" })).toBeVisible();
  await page.getByRole("button", { name: "Add" }).click();
  await page.getByLabel("Role ID (lowercase and hyphens)").fill("browser-editor");
  await page.getByLabel("Readable name").fill("Browser Editor");
  await page.getByRole("button", { name: "Create role" }).click();
  await expect(page.getByRole("button", { name: /Browser Editor/ })).toBeVisible();

  await page.goto("/admin/users");
  await page.getByRole("button", { name: "Add user" }).click();
  await page.getByLabel("Email").fill("browser-editor@example.test");
  await page.getByLabel("Display name").fill("Browser Editor");
  await page.getByLabel("Temporary password (12+ characters)").fill(password);
  await page.getByLabel("Initial role").selectOption("browser-editor");
  await page.getByRole("button", { name: "Create user" }).click();
  await expect(page.getByText("browser-editor@example.test")).toBeVisible();

  const createdRow = page.getByRole("row").filter({ hasText: "browser-editor@example.test" });
  await createdRow.getByRole("button", { name: "Disable" }).click();
  await expect(createdRow.getByText("inactive")).toBeVisible();
});

test("unauthorized identity cannot expose User or Role management", async ({ page }) => {
  await login(page, "viewer@example.test");
  await page.goto("/admin/users");
  await expect(page.getByText("You do not have permission")).toBeVisible();
  const storage = await page.evaluate(() => ({ local: Object.keys(localStorage), session: Object.keys(sessionStorage) }));
  expect(storage).toEqual({ local: [], session: [] });
});

test("mobile administration keeps account and navigation controls accessible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await expect(page.getByRole("button", { name: "Account" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open menu" })).toBeVisible();
});

test("authorized operator manages a Plugin-owned application through real contracts", async ({ page }) => {
  await login(page);
  await page.goto("/admin/applications");
  await expect(page.getByRole("heading", { name: "Applications" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Products/ })).toBeVisible();
  await page.getByRole("button", { name: "Add record" }).click();
  await page.getByLabel("name").fill("Browser catalog item");
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByText("Application record created.")).toBeVisible();
  const row = page.getByRole("row").filter({ hasText: "Browser catalog item" });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Edit" }).click();
  await page.getByLabel("name").fill("Updated browser item");
  await page.getByRole("button", { name: "Save record" }).click();
  await expect(page.getByText("Updated browser item")).toBeVisible();
});
