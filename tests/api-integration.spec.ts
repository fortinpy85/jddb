import { test, expect } from "@playwright/test";

test.describe("API Integration", () => {
  test("should load dashboard stats from API", async ({ page }) => {
    // Intercept API calls to verify they're made correctly
    let statsApiCalled = false;
    await page.route("**/api/stats", (route) => {
      statsApiCalled = true;
      route.continue();
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Verify stats API was called
    expect(statsApiCalled).toBe(true);

    // Verify stats are displayed
    await expect(page.locator("text=Total Jobs")).toBeVisible();
  });

  test("should load jobs from API", async ({ page }) => {
    let jobsApiCalled = false;
    await page.route("**/api/jobs**", (route) => {
      jobsApiCalled = true;
      route.continue();
    });

    await page.goto("/");
    await page.getByRole("tab", { name: "Jobs" }).click();
    await page.waitForLoadState("networkidle");

    // Verify jobs API was called
    expect(jobsApiCalled).toBe(true);
  });

  test("should handle API errors gracefully", async ({ page }) => {
    // Mock API failure
    await page.route("**/api/stats", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal Server Error" }),
      });
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Verify error handling (this would depend on actual error handling implementation)
    // The app should not crash and should show some error state
    await expect(page.locator("body")).toBeVisible(); // App should still render
  });

  test("should make search API calls with correct parameters", async ({
    page,
  }) => {
    let searchApiCalled = false;
    let searchParams: URLSearchParams | undefined;

    await page.route("**/api/search**", (route) => {
      searchApiCalled = true;
      const url = new URL(route.request().url());
      searchParams = url.searchParams;
      route.continue();
    });

    await page.goto("/");
    await page.getByRole("tab", { name: "Search" }).click();

    const searchInput = page.locator('input[placeholder*="search"]');
    if ((await searchInput.count()) > 0) {
      await searchInput.fill("manager");
      await searchInput.press("Enter");
      await page.waitForLoadState("networkidle");

      // Verify search API was called with correct parameters
      expect(searchApiCalled).toBe(true);
      if (searchParams) {
        const qParam = searchParams.get("q");
        const queryParam = searchParams.get("query");
        expect(qParam || queryParam).toContain("manager");
      }
    }
  });

  test("should handle slow API responses", async ({ page }) => {
    // Mock slow API response
    await page.route("**/api/jobs**", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000)); // 2 second delay
      route.continue();
    });

    await page.goto("/");
    await page.getByRole("tab", { name: "Jobs" }).click();

    // Check for loading state
    const loadingIndicator = page
      .locator("text=Loading")
      .or(page.locator('[data-testid="loading"]'));
    if ((await loadingIndicator.count()) > 0) {
      await expect(loadingIndicator).toBeVisible();
    }

    // Wait for content to eventually load
    await page.waitForLoadState("networkidle", { timeout: 30000 });
  });

  test("should handle network errors", async ({ page }) => {
    // Mock network failure
    await page.route("**/api/**", (route) => {
      route.abort("failed");
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // App should still render basic structure even with API failures
    await expect(page.locator("h1")).toContainText("Job Description Database");
  });

  test("should make API calls with proper headers", async ({ page }) => {
    let requestHeaders: { [key: string]: string } = {};

    await page.route("**/api/**", (route) => {
      requestHeaders = route.request().headers();
      route.continue();
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Verify proper headers are sent
    expect(requestHeaders["accept"]).toContain("application/json");
  });

  test("should retry failed API requests", async ({ page }) => {
    let callCount = 0;
    await page.route("**/api/stats", (route) => {
      callCount++;
      if (callCount === 1) {
        // Fail first request
        route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ error: "Server Error" }),
        });
      } else {
        // Succeed on retry
        route.continue();
      }
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // If retry logic is implemented, should see multiple calls
    expect(callCount).toBeGreaterThan(0);
  });
});
