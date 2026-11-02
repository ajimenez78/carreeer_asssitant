import { expect, test } from "@playwright/test";

test("entry page is readable and keyboard accessible", async ({ page }) => {
  const browserErrors: string[] = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));

  await page.goto("/");

  await expect(page).toHaveTitle("Your ideal job | Career assistant");
  await expect(page.getByRole("heading", { level: 1, name: "Define your ideal job." })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Main navigation" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Start with what matters." })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Mock preview" })).toContainText("Requests are mocked");

  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();

  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(browserErrors).toEqual([]);
});
