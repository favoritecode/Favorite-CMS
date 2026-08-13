import { expect, test } from "@playwright/test";

test("renders the Phase 0 frontend skeleton", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Favorite CMS" })).toBeVisible();
});

