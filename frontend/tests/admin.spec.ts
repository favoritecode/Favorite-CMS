import { expect, test } from "@playwright/test";

const password = "correct horse battery staple";

async function login(page: import("@playwright/test").Page, email: string) {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Admin dashboard" })).toBeVisible();
}

test("unauthenticated Admin navigation is denied by the real session boundary", async ({ page }) => {
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "Admin sign in" })).toBeVisible();
});

test("real Admin login, explicit Permission navigation, cookie safety, and logout revocation", async ({ page, context }) => {
  await login(page, "operator@example.test");
  const link = page.getByRole("link", { name: "Test management" });
  await expect(link).toHaveAttribute("href", "/admin/test-management");
  const cookies = await context.cookies();
  const session = cookies.find(cookie => cookie.name === "favorite_admin_session");
  expect(session?.httpOnly).toBe(true);
  expect(session?.sameSite).toBe("Strict");
  expect(await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length }))).toEqual({ local: 0, session: 0 });
  await expect(page.locator("body")).not.toContainText(password);
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("heading", { name: "Admin sign in" })).toBeVisible();
  expect((await context.cookies()).some(cookie => cookie.name === "favorite_admin_session")).toBe(false);
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "Admin sign in" })).toBeVisible();
});

test("authenticated but unauthorized Admin receives an empty permission-filtered workspace", async ({ page }) => {
  await login(page, "viewer@example.test");
  await expect(page.getByText("No management modules are available for this account.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Test management" })).toHaveCount(0);
});

test("invalid credentials render a safe real backend error", async ({ page }) => {
  await page.goto("/admin/login");
  await page.getByLabel("Email").fill("operator@example.test");
  await page.getByLabel("Password").fill("wrong password");
  await page.getByRole("button", { name: "Sign in" }).click();
  const alert = page.getByText("Authentication failed", { exact: true });
  await expect(alert).toContainText("Authentication failed");
  await expect(alert).not.toContainText("password_hash");
  await expect(alert).not.toContainText("Traceback");
});
