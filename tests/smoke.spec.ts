import { test, expect } from "@playwright/test";

test.describe("Smoke Tests", () => {
  test("application loads successfully", async ({ page }) => {
    await page.goto("/");

    // Basic application structure should be present (use first h1 to avoid strict mode)
    await expect(page.locator("h1").first()).toContainText(
      /Job Description Database|JDDB|Dashboard/,
    );
    await expect(page.getByRole("tab", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Jobs" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Upload" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Search" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Compare" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Statistics" })).toBeVisible();
  });

  test("all tabs are accessible", async ({ page }) => {
    await page.goto("/");

    // Navigate to each tab and verify they load
    const tabs = ["Jobs", "Upload", "Search", "Compare", "Statistics"];

    for (const tab of tabs) {
      await page.getByRole("tab", { name: tab }).click();
      await page.waitForLoadState("networkidle");
      await expect(page.getByRole("tab", { selected: true })).toContainText(
        tab,
      );
    }
  });

  test("no console errors on page load", async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Allow some common non-critical errors but fail on critical ones
    const criticalErrors = consoleErrors.filter(
      (error) =>
        !error.includes("favicon") &&
        !error.includes("404") &&
        !error.includes("network") &&
        !error.includes("Heading order") &&
        !error.includes("landmarks"),
    );

    expect(criticalErrors).toHaveLength(0);
  });

  test("page is responsive", async ({ page }) => {
    await page.goto("/");

    // Test mobile viewport (use first h1 to avoid strict mode)
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator("h1").first()).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator("h1").first()).toBeVisible();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator("h1").first()).toBeVisible();
  });
});
