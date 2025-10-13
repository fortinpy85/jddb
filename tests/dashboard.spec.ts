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
    // Mock API response for statistics
    await page.route("**/api/jobs/stats", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total_jobs: 150,
          completed: 120,
          processing: 25,
          need_review: 5,
          classification_distribution: {
            "EX-01": 80,
            "EX-02": 50,
            "EX-03": 20,
          },
          language_distribution: { EN: 100, FR: 50 },
        }),
      });
    });

    // Wait for stats to load
    await page.waitForLoadState("networkidle");

    // Check all stats cards are present with values
    await expect(page.locator("text=Total Jobs").first()).toBeVisible();
    await expect(page.locator("text=150").first()).toBeVisible();
    await expect(page.locator("text=Completed").first()).toBeVisible();
    await expect(page.locator("text=120").first()).toBeVisible();
    await expect(page.locator("text=Need Review").first()).toBeVisible();
    await expect(page.locator("text=5").first()).toBeVisible();
    await expect(page.locator("text=Processing").first()).toBeVisible();
    await expect(page.locator("text=25").first()).toBeVisible();
  });

  test("should display charts and recent jobs", async ({ page }) => {
    // Mock recent jobs API response
    await page.route("**/api/jobs/**", async (route) => {
      const url = route.request().url();
      if (url.includes("recent")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            jobs: [
              {
                id: 1,
                title: "Director, Business Analysis",
                job_number: "123456",
                processed_date: "2024-01-15T10:00:00Z",
              },
              {
                id: 2,
                title: "Senior Analyst",
                job_number: "789012",
                processed_date: "2024-01-14T09:00:00Z",
              },
            ],
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.waitForLoadState("networkidle");

    // Check classification chart
    await expect(page.locator("text=Jobs by Classification")).toBeVisible();

    // Check language chart
    await expect(page.locator("text=Jobs by Language")).toBeVisible();

    // Check recent jobs section
    await expect(page.locator("text=Recent Job Descriptions")).toBeVisible();

    // Check that recent jobs display properly
    await expect(
      page.locator("text=Director, Business Analysis"),
    ).toBeVisible();
    await expect(page.locator("text=Senior Analyst")).toBeVisible();
  });

  test("should display quick actions", async ({ page }) => {
    // Check quick action buttons
    await expect(page.locator("text=Upload Files")).toBeVisible();
    await expect(page.locator("text=Browse Jobs")).toBeVisible();
    await expect(page.locator("text=Search Jobs")).toBeVisible();
    await expect(page.locator("text=Compare Jobs")).toBeVisible();
  });

  test("should navigate to different tabs via quick actions", async ({
    page,
  }) => {
    // Navigate to upload via quick action
    await page.click("text=Upload Files");
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Upload",
    );

    // Navigate to jobs via quick action
    await page.getByRole("button", { name: /browse jobs/i }).click();
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Jobs",
    );

    // Navigate to search via quick action
    await page.click("text=Search Jobs");
    await expect(page.getByRole("tab", { selected: true })).toContainText(
      "Search",
    );

    // Navigate to compare via quick action
    await page.click("text=Compare Jobs");
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
