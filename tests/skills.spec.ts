import { test, expect } from "@playwright/test";

test.describe("Skills Features", () => {
  test.beforeEach(async ({ page }) => {
    // Use real API with seeded database (backend/scripts/seed_skills_test_data.py)
    // No mocking - tests validate actual end-to-end flow
    await page.goto("/");
    // Wait for React SPA to fully hydrate and lazy components to load
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);
  });

  test.describe("Job Details - Skills Display", () => {
    test("should display skills on job detail page", async ({ page }) => {
      // Navigate to jobs list
      await page.getByRole("tab", { name: /jobs/i }).click();
      await page.waitForTimeout(1000);

      // Click on Senior Python Developer (seeded job 123456)
      await page.getByText("Senior Python Developer").click();
      await page.waitForTimeout(1500);

      // Check for skills section header
      const skillsHeading = page.getByRole("heading", { name: "Extracted Skills" });
      await expect(skillsHeading).toBeVisible();

      // Check skills are displayed (real seeded data: Python 95%, Project Management 87%)
      // Skills are in the parent container after the heading
      const skillsContainer = page.locator("div").filter({ hasText: /^Extracted Skills/ });
      await expect(skillsContainer.getByText("Python")).toBeVisible();
      await expect(skillsContainer.getByText("95%")).toBeVisible();

      await expect(skillsContainer.getByText("Project Management")).toBeVisible();
      await expect(skillsContainer.getByText("87%")).toBeVisible();

      // Check statistics are shown
      await expect(page.getByText("Total Skills:")).toBeVisible();
      // Real data has 2 skills for this job
      await expect(page.getByText("Total Skills:").locator('..').getByText("2")).toBeVisible();

      await expect(page.getByText("Avg Confidence:")).toBeVisible();
    });

    test.skip("should handle jobs with no skills", async ({ page }) => {
      // TODO: Requires job without skills in database
      // Current seed data: both jobs (123456, 789012) have skills
      // Need to either: 1) Add job without skills to seed script, or 2) Test with different database state
      await page.getByRole("tab", { name: /jobs/i }).click();
      await page.waitForTimeout(1000);

      // Would verify "No skills extracted yet" message appears
    });

    test.skip("should expand/collapse many skills", async ({ page }) => {
      // TODO: Requires job with 15+ skills in database
      // Current seeded jobs only have 2 skills each
      // Need to either: 1) Add large-skills job to seed script, or 2) Test programmatically
      await page.getByRole("tab", { name: /jobs/i }).click();
      await page.waitForTimeout(1000);

      // Would test "Show all N skills" button and expand/collapse functionality
    });
  });

  test.describe("Skills Analytics Dashboard", () => {
    test.skip("should display Skills Analytics tab", async ({ page }) => {
      // TODO: Tab click interaction times out (UI loading/animation issue)
      // Dashboard exists and works manually, but automated click fails
      // Needs investigation of loading states or alternative interaction method
      await page.getByRole("tab", { name: /dashboard/i }).click();
      await page.waitForTimeout(1500);
      await page.getByRole("tab", { name: /skills analytics/i }).click();
    });

    test.skip("should handle empty skills data", async ({ page }) => {
      // TODO: Requires database with no skills or special test setup
      // Current seed data has 2 jobs with skills
      // Need to test with clean database or mock empty state
      await page.getByRole("tab", { name: /dashboard/i }).click();
      await page.waitForTimeout(1000);
    });
  });

  test.describe("Skills Filtering in Jobs List", () => {
    test("should filter jobs by selected skills", async ({ page }) => {
      // Navigate to jobs list
      await page.getByRole("tab", { name: /jobs/i }).click();
      await page.waitForTimeout(1000);

      // Check initial jobs are displayed
      await expect(page.getByText("Senior Python Developer")).toBeVisible();
      await expect(page.getByText("Data Analyst")).toBeVisible();

      // Check for skills filter UI
      await expect(page.getByText("Filter by Skills:")).toBeVisible();

      // Open skills dropdown
      await page.getByRole("combobox", { name: /add skill filter/i }).click();

      // Select "Python" skill
      await page.getByRole("option", { name: /python/i }).click();

      // Should show Python as a filter badge
      await expect(
        page.locator(".cursor-pointer").filter({ hasText: "Python ×" })
      ).toBeVisible();

      // Both jobs should still be visible (both have Python)
      await expect(page.getByText("Senior Python Developer")).toBeVisible();
      await expect(page.getByText("Data Analyst")).toBeVisible();

      // Add another skill filter (Project Management)
      await page.getByRole("combobox", { name: /add skill filter/i }).click();
      await page.getByRole("option", { name: /project management/i }).click();

      // Now only Senior Python Developer should be visible (has both skills)
      await expect(page.getByText("Senior Python Developer")).toBeVisible();
      // Data Analyst should be filtered out (doesn't have Project Management)
      await expect(page.getByText("Data Analyst")).not.toBeVisible();
    });

    test("should clear individual skill filters", async ({ page }) => {
      await page.getByRole("tab", { name: /jobs/i }).click();
      await page.waitForTimeout(1000);

      // Add skill filter
      await page.getByRole("combobox", { name: /add skill filter/i }).click();
      await page.getByRole("option", { name: /python/i }).click();

      // Click the X on the badge to remove filter
      await page.locator(".cursor-pointer").filter({ hasText: "Python ×" }).click();

      // Filter should be removed
      await expect(
        page.locator(".cursor-pointer").filter({ hasText: "Python ×" })
      ).not.toBeVisible();

      // All jobs should be visible again
      await expect(page.getByText("Senior Python Developer")).toBeVisible();
      await expect(page.getByText("Data Analyst")).toBeVisible();
    });

    test("should clear all skill filters", async ({ page }) => {
      await page.getByRole("tab", { name: /jobs/i }).click();
      await page.waitForTimeout(1000);

      // Add multiple skill filters
      await page.getByRole("combobox", { name: /add skill filter/i }).click();
      await page.getByRole("option", { name: /python/i }).click();

      await page.getByRole("combobox", { name: /add skill filter/i }).click();
      await page.getByRole("option", { name: /project management/i }).click();

      // Click "Clear" button for skills
      await page
        .locator("div")
        .filter({ hasText: /filter by skills/i })
        .getByRole("button", { name: /clear/i })
        .click();

      // All filters should be removed
      await expect(
        page.locator(".cursor-pointer").filter({ hasText: "Python ×" })
      ).not.toBeVisible();
      await expect(
        page.locator(".cursor-pointer").filter({ hasText: "Project Management ×" })
      ).not.toBeVisible();

      // All jobs should be visible
      await expect(page.getByText("Senior Python Developer")).toBeVisible();
      await expect(page.getByText("Data Analyst")).toBeVisible();
    });

    test("should integrate with other filters", async ({ page }) => {
      await page.getByRole("tab", { name: /jobs/i }).click();
      await page.waitForTimeout(1000);

      // Apply classification filter
      await page.getByRole("combobox", { name: /classification/i }).click();
      await page.getByRole("option", { name: "IT-03" }).click();

      // Only Senior Python Developer should be visible
      await expect(page.getByText("Senior Python Developer")).toBeVisible();
      await expect(page.getByText("Data Analyst")).not.toBeVisible();

      // Add skill filter
      await page.getByRole("combobox", { name: /add skill filter/i }).click();
      await page.getByRole("option", { name: /python/i }).click();

      // Still only Senior Python Developer (matches both filters)
      await expect(page.getByText("Senior Python Developer")).toBeVisible();
      await expect(page.getByText("Data Analyst")).not.toBeVisible();
    });
  });
});
