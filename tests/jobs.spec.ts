import { test, expect } from "@playwright/test";
import {
  mockApiResponse,
  mockJobsList,
  waitForApiCall,
  waitForLoading,
} from "./utils/test-helpers";

test.describe("Jobs Management", () => {
  test.beforeEach(async ({ page }) => {
    // Mock jobs API response
    await mockApiResponse(page, "**/api/jobs/**", mockJobsList);

    await page.goto("/");
    await page.getByRole("tab", { name: "Jobs" }).click();
    await waitForLoading(page);
  });

  test("should display jobs list", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    // Check for jobs list container
    await expect(
      page
        .locator('[data-testid="jobs-list"]')
        .or(page.locator(".jobs-container")),
    ).toBeVisible();

    // Check for filter controls
    await expect(
      page
        .locator("text=Filter")
        .or(page.locator('input[placeholder*="filter"]')),
    ).toBeVisible();
  });

  test("should display job cards with required information", async ({
    page,
  }) => {
    await waitForApiCall(page, "/api/jobs");

    // Check for job information from mocked data
    await expect(
      page.locator("text=Director, Business Analysis"),
    ).toBeVisible();
    await expect(page.locator("text=Senior Analyst")).toBeVisible();
    await expect(page.locator("text=123456")).toBeVisible();
    await expect(page.locator("text=789012")).toBeVisible();
    await expect(page.locator("text=EX-01")).toBeVisible();
    await expect(page.locator("text=EX-02")).toBeVisible();

    // Check language indicators
    await expect(page.locator("text=EN")).toBeVisible();
    await expect(page.locator("text=FR")).toBeVisible();

    // Check sections count
    await expect(page.locator("text=5 sections")).toBeVisible();
    await expect(page.locator("text=3 sections")).toBeVisible();
  });

  test("should filter jobs by classification", async ({ page }) => {
    // Wait for initial load
    await waitForApiCall(page, "/api/jobs");

    // Mock filtered results
    await mockApiResponse(page, "**/api/jobs/**", {
      jobs: [mockJobsList.jobs[0]], // Only EX-01 job
      total: 1,
      page: 1,
      pages: 1,
    });

    // Click on classification filter dropdown
    await page.getByText("All Classifications").click();

    // Select EX-01 classification
    await page.getByText("EX-01").click();

    // Verify filtered results - should only show Director job
    await expect(
      page.locator("text=Director, Business Analysis"),
    ).toBeVisible();
    await expect(page.locator("text=Senior Analyst")).not.toBeVisible();

    // Check total count updated
    await expect(page.locator("text=1 job")).toBeVisible();
  });

  test("should navigate to job details", async ({ page }) => {
    // Mock job details API response
    await mockApiResponse(page, "**/api/jobs/1", {
      id: 1,
      job_number: "123456",
      title: "Director, Business Analysis",
      classification: "EX-01",
      language: "EN",
      sections: [
        {
          section_type: "GENERAL_ACCOUNTABILITY",
          section_content: "Test content",
          section_order: 1,
        },
        {
          section_type: "SPECIFIC_ACCOUNTABILITIES",
          section_content: "Test content",
          section_order: 2,
        },
      ],
    });

    await waitForApiCall(page, "/api/jobs");

    // Click on first job
    await page.locator("text=Director, Business Analysis").click();

    // Verify navigation to job details
    await expect(page.locator("text=Job Details")).toBeVisible();
    await expect(
      page.locator("text=Director, Business Analysis"),
    ).toBeVisible();
    await expect(page.locator("text=123456")).toBeVisible();

    // Check for sections
    await expect(page.locator("text=GENERAL_ACCOUNTABILITY")).toBeVisible();
    await expect(page.locator("text=SPECIFIC_ACCOUNTABILITIES")).toBeVisible();
  });

  test("should return to jobs list from job details", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    const jobCards = page
      .locator('[data-testid="job-card"]')
      .or(page.locator(".job-card"))
      .or(page.locator('[role="button"]'));
    const jobCount = await jobCards.count();

    if (jobCount > 0) {
      // Navigate to job details
      await jobCards.first().click();

      // Click back button
      const backButton = page
        .locator("text=Back")
        .or(page.locator('[data-action="back"]'));
      await backButton.click();

      // Verify return to jobs list
      await expect(
        page
          .locator('[data-testid="jobs-list"]')
          .or(page.locator(".jobs-container")),
      ).toBeVisible();
    }
  });

  test("should handle job list loading states", async ({ page }) => {
    // Check for loading indicators
    const loadingIndicator = page
      .locator("text=Loading")
      .or(page.locator('[data-testid="loading"]'))
      .or(page.locator(".loading"));

    // Loading indicator might appear briefly, so we use a short timeout
    if ((await loadingIndicator.count()) > 0) {
      await expect(loadingIndicator).toBeVisible();
    }

    // Wait for content to load
    await page.waitForLoadState("networkidle");
  });
});
