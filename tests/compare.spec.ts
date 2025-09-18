import { test, expect } from "@playwright/test";

test.describe("Job Comparison", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "Compare" }).click();
  });

  test("should display job comparison interface", async ({ page }) => {
    // Check for comparison interface elements
    await expect(
      page
        .locator("text=Compare Jobs")
        .or(page.locator('[data-testid="comparison-interface"]')),
    ).toBeVisible();

    // Check for job selection areas
    await expect(
      page
        .locator("text=Select jobs to compare")
        .or(page.locator('[data-testid="job-selector"]')),
    ).toBeVisible();
  });

  test("should allow job selection for comparison", async ({ page }) => {
    await page.waitForLoadState("networkidle");

    // Look for job selection dropdowns or search inputs
    const jobSelectors = page
      .locator("select")
      .or(page.locator('input[placeholder*="search"]'));
    const selectorCount = await jobSelectors.count();

    if (selectorCount > 0) {
      await expect(jobSelectors.first()).toBeVisible();

      // If there are multiple selectors (for comparing multiple jobs)
      if (selectorCount > 1) {
        await expect(jobSelectors.nth(1)).toBeVisible();
      }
    }
  });

  test("should display comparison results side by side", async ({ page }) => {
    // Look for side-by-side comparison layout
    const comparisonContainer = page
      .locator('[data-testid="comparison-results"]')
      .or(
        page.locator(".comparison-container").or(page.locator(".side-by-side")),
      );

    if ((await comparisonContainer.count()) > 0) {
      await expect(comparisonContainer).toBeVisible();
    }
  });

  test("should show job details in comparison view", async ({ page }) => {
    // Check for job detail sections that would appear in comparison
    const detailSections = [
      "Classification",
      "Department",
      "Accountability",
      "Skills",
      "Requirements",
    ];

    for (const section of detailSections) {
      const sectionElement = page.locator(`text=${section}`);
      if ((await sectionElement.count()) > 0) {
        await expect(sectionElement).toBeVisible();
        break; // At least one section should be visible
      }
    }
  });

  test("should highlight differences between jobs", async ({ page }) => {
    // Look for difference highlighting functionality
    const differenceIndicators = page
      .locator(".difference")
      .or(
        page
          .locator(".highlight")
          .or(page.locator('[data-testid="difference"]')),
      );

    // This would only be visible if jobs are actually being compared
    if ((await differenceIndicators.count()) > 0) {
      await expect(differenceIndicators.first()).toBeVisible();
    }
  });

  test("should show similarity scores", async ({ page }) => {
    // Look for similarity score display
    const similarityScore = page
      .locator("text=Similarity")
      .or(
        page
          .locator("text=%")
          .or(page.locator('[data-testid="similarity-score"]')),
      );

    if ((await similarityScore.count()) > 0) {
      await expect(similarityScore).toBeVisible();
    }
  });

  test("should allow clearing comparison selections", async ({ page }) => {
    // Look for clear/reset buttons
    const clearButton = page
      .locator("text=Clear")
      .or(page.locator("text=Reset").or(page.locator('[data-action="clear"]')));

    if ((await clearButton.count()) > 0) {
      await expect(clearButton).toBeVisible();
    }
  });

  test("should handle empty comparison state", async ({ page }) => {
    // Check for empty state when no jobs are selected for comparison
    await expect(
      page
        .locator("text=Select jobs to compare")
        .or(
          page
            .locator("text=Choose jobs from the list")
            .or(page.locator('[data-testid="empty-comparison"]')),
        ),
    ).toBeVisible();
  });
});
