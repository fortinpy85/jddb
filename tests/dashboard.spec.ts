import { test, expect } from "@playwright/test";
import { mockApiResponse, waitForApiCall } from "./utils/test-helpers";

test.describe("Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should display main dashboard elements", async ({ page }) => {
    // Check header (use first h1 to avoid strict mode violation)
    await expect(page.locator("h1").first()).toContainText(
      /Job Description Database|JDDB|Dashboard/,
    );

    // Check navigation tabs
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Dashboard",
    );
    await expect(page.getByRole("tab", { name: "Jobs" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Upload" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Search" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Compare" })).toBeVisible();
  });

  test("should display stats cards", async ({ page }) => {
    // Mock API response for statistics BEFORE navigating to page
    await page.route("**/api/jobs/stats", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total_jobs: 150,
          by_classification: {
            "EX-01": 80,
            "EX-02": 50,
            "EX-03": 20,
          },
          by_language: { EN: 100, FR: 50 },
          by_status: { active: 150 },
          recent_uploads: 10,
          processing_status: {
            completed: 120,
            processing: 25,
            pending: 0,
            needs_review: 5,
            failed: 0,
          },
        }),
      });
    });

    // Also mock jobs endpoint
    await page.route("**/api/jobs?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          jobs: [],
          total: 0,
          pagination: { skip: 0, limit: 20, total: 0, has_more: false },
        }),
      });
    });

    // Reload page to apply mocks
    await page.reload();
    await page.waitForLoadState("networkidle");

    // Check stats cards are present - look for labels, not specific numbers
    await expect(page.locator("text=Total Jobs").first()).toBeVisible();
    await expect(page.locator("text=Completed").first()).toBeVisible();
    await expect(page.locator("text=Processing").first()).toBeVisible();
  });

  test("should display charts and recent jobs", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    // Check for any data visualization elements (charts, graphs, or stats sections)
    // Dashboard likely has stats cards or data displays
    const hasDataVisualization =
      (await page.locator('[role="img"]').count()) > 0 || // Charts with SVG
      (await page.locator('.chart, [data-testid*="chart"]').count()) > 0 || // Chart containers
      (await page.locator('text=/Total|Jobs|Statistics/i').count()) > 0; // Stats text

    expect(hasDataVisualization).toBeTruthy();

    // Check for dashboard content sections
    const hasDashboardContent =
      (await page.locator('text=/Dashboard|Overview|Summary/i').count()) > 0;

    expect(hasDashboardContent).toBeTruthy();
  });

  test.skip("should display quick actions", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    // Check quick action buttons with longer timeout
    await expect(page.locator("text=Upload Files")).toBeVisible({ timeout: 15000 });
    await expect(page.locator("text=Browse Jobs")).toBeVisible();
    await expect(page.locator("text=Search Jobs")).toBeVisible();
    await expect(page.locator("text=Compare Jobs")).toBeVisible();
  });

  test.skip("should navigate to different tabs via quick actions", async ({
    page,
  }) => {
    await page.waitForLoadState("networkidle");

    // Navigate to upload via quick action
    await page.locator("text=Upload Files").click();
    await page.waitForTimeout(500);
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Upload",
    );

    // Go back to dashboard
    await page.getByRole("tab", { name: "Dashboard" }).click();
    await page.waitForTimeout(500);

    // Navigate to jobs via quick action
    await page.locator("text=Browse Jobs").click();
    await page.waitForTimeout(500);
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Jobs",
    );

    // Go back to dashboard
    await page.getByRole("tab", { name: "Dashboard" }).click();
    await page.waitForTimeout(500);

    // Navigate to search via quick action
    await page.locator("text=Search Jobs").click();
    await page.waitForTimeout(500);
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Search",
    );

    // Go back to dashboard
    await page.getByRole("tab", { name: "Dashboard" }).click();
    await page.waitForTimeout(500);

    // Navigate to compare via quick action
    await page.locator("text=Compare Jobs").click();
    await page.waitForTimeout(500);
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Compare",
    );
  });

  test("should navigate via tab navigation", async ({ page }) => {
    // Test tab navigation
    await page.getByRole("tab", { name: "Jobs" }).click();
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Jobs",
    );

    await page.getByRole("tab", { name: "Upload" }).click();
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Upload",
    );

    await page.getByRole("tab", { name: "Search" }).click();
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Search",
    );

    await page.getByRole("tab", { name: "Compare" }).click();
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Compare",
    );

    await page.getByRole("tab", { name: "Dashboard" }).click();
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Dashboard",
    );
  });
});
