import { test, expect } from "@playwright/test";

test.describe("Skills Features", () => {
  test.beforeEach(async ({ page }) => {
    // Mock jobs list with skills
    await page.route("**/api/jobs?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          jobs: [
            {
              id: 1,
              job_number: "123456",
              title: "Senior Python Developer",
              classification: "IT-03",
              language: "en",
              created_at: "2024-01-15T10:00:00Z",
              skills: [
                {
                  id: 1,
                  lightcast_id: "KS123456",
                  name: "Python",
                  skill_type: "Hard Skill",
                  confidence: 0.95,
                },
                {
                  id: 2,
                  lightcast_id: "KS789012",
                  name: "Project Management",
                  skill_type: "Soft Skill",
                  confidence: 0.87,
                },
              ],
            },
            {
              id: 2,
              job_number: "789012",
              title: "Data Analyst",
              classification: "EC-05",
              language: "en",
              created_at: "2024-01-14T09:00:00Z",
              skills: [
                {
                  id: 3,
                  lightcast_id: "KS345678",
                  name: "Data Analysis",
                  skill_type: "Hard Skill",
                  confidence: 0.92,
                },
                {
                  id: 1,
                  lightcast_id: "KS123456",
                  name: "Python",
                  skill_type: "Hard Skill",
                  confidence: 0.88,
                },
              ],
            },
          ],
          pagination: {
            skip: 0,
            limit: 100,
            total: 2,
            has_more: false,
          },
        }),
      });
    });

    await page.goto("/");
  });

  test.describe("Job Details - Skills Display", () => {
    test("should display skills on job detail page", async ({ page }) => {
      // Mock job detail with skills
      await page.route("**/api/jobs/1?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            job_number: "123456",
            title: "Senior Python Developer",
            classification: "IT-03",
            language: "en",
            skills: [
              {
                id: 1,
                lightcast_id: "KS123456",
                name: "Python",
                skill_type: "Hard Skill",
                confidence: 0.95,
              },
              {
                id: 2,
                lightcast_id: "KS789012",
                name: "Project Management",
                skill_type: "Soft Skill",
                confidence: 0.87,
              },
              {
                id: 4,
                lightcast_id: "KS456789",
                name: "Agile",
                skill_type: "Soft Skill",
                confidence: 0.65,
              },
            ],
            sections: [],
            metadata: {},
          }),
        });
      });

      // Navigate to jobs list
      await page.getByRole("button", { name: /jobs/i }).click();

      // Click on a job to view details
      await page.getByText("Senior Python Developer").click();

      // Wait for job details to load
      await page.waitForLoadState("networkidle");

      // Check for skills section header
      await expect(page.getByText("Extracted Skills")).toBeVisible();

      // Check skills are displayed as tags
      await expect(page.getByText("Python")).toBeVisible();
      await expect(page.getByText("95%")).toBeVisible(); // Confidence score

      await expect(page.getByText("Project Management")).toBeVisible();
      await expect(page.getByText("87%")).toBeVisible();

      await expect(page.getByText("Agile")).toBeVisible();
      await expect(page.getByText("65%")).toBeVisible();

      // Check statistics are shown
      await expect(page.getByText("Total Skills:")).toBeVisible();
      await expect(page.getByText("3")).toBeVisible();

      await expect(page.getByText("Avg Confidence:")).toBeVisible();
    });

    test("should handle jobs with no skills", async ({ page }) => {
      await page.route("**/api/jobs/2?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 2,
            job_number: "789012",
            title: "Data Analyst",
            classification: "EC-05",
            language: "en",
            skills: [],
            sections: [],
            metadata: {},
          }),
        });
      });

      await page.getByRole("button", { name: /jobs/i }).click();
      await page.getByText("Data Analyst").click();
      await page.waitForLoadState("networkidle");

      // Should not show skills section or show "No skills"
      const skillsSection = page.getByText("Extracted Skills");
      if (await skillsSection.isVisible()) {
        await expect(page.getByText("No skills extracted yet")).toBeVisible();
      }
    });

    test("should expand/collapse many skills", async ({ page }) => {
      // Create job with many skills
      const manySkills = Array.from({ length: 25 }, (_, i) => ({
        id: i + 1,
        lightcast_id: `KS${1000 + i}`,
        name: `Skill ${i + 1}`,
        skill_type: "Hard Skill",
        confidence: 0.8 - i * 0.01,
      }));

      await page.route("**/api/jobs/1?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            job_number: "123456",
            title: "Senior Python Developer",
            classification: "IT-03",
            language: "en",
            skills: manySkills,
            sections: [],
            metadata: {},
          }),
        });
      });

      await page.getByRole("button", { name: /jobs/i }).click();
      await page.getByText("Senior Python Developer").click();
      await page.waitForLoadState("networkidle");

      // Should show "Show all" button for many skills
      await expect(
        page.getByRole("button", { name: /show all \d+ skills/i })
      ).toBeVisible();

      // Click to expand
      await page.getByRole("button", { name: /show all/i }).click();

      // Should now show "Show fewer" button
      await expect(
        page.getByRole("button", { name: /show fewer/i })
      ).toBeVisible();

      // All skills should be visible
      await expect(page.getByText("Skill 25")).toBeVisible();
    });
  });

  test.describe("Skills Analytics Dashboard", () => {
    test("should display Skills Analytics tab", async ({ page }) => {
      // Mock skills stats
      await page.route("**/api/analytics/skills/stats", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            total_unique_skills: 150,
            total_skill_associations: 450,
            jobs_with_skills: 120,
            total_jobs: 150,
            skills_coverage_percentage: 80.0,
            avg_skills_per_job: 3.0,
            avg_confidence_score: 82.5,
          }),
        });
      });

      // Mock top skills
      await page.route("**/api/analytics/skills/top?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            total_jobs: 150,
            top_skills: [
              { skill_name: "Python", job_count: 45, percentage: 30.0 },
              { skill_name: "Project Management", job_count: 38, percentage: 25.3 },
              { skill_name: "Data Analysis", job_count: 35, percentage: 23.3 },
            ],
          }),
        });
      });

      // Mock skill types
      await page.route("**/api/analytics/skills/types", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            skill_types: [
              { type: "Hard Skill", skill_count: 100, job_count: 110, percentage: 66.7 },
              { type: "Soft Skill", skill_count: 50, job_count: 80, percentage: 33.3 },
            ],
            total_types: 2,
          }),
        });
      });

      // Mock skills inventory
      await page.route("**/api/analytics/skills/inventory?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            skills: [
              {
                id: 1,
                lightcast_id: "KS123456",
                name: "Python",
                skill_type: "Hard Skill",
                job_count: 45,
                avg_confidence: 0.92,
              },
              {
                id: 2,
                lightcast_id: "KS789012",
                name: "Project Management",
                skill_type: "Soft Skill",
                job_count: 38,
                avg_confidence: 0.85,
              },
            ],
            total: 150,
            limit: 20,
            offset: 0,
          }),
        });
      });

      // Navigate to Dashboard
      await page.getByRole("button", { name: /dashboard/i }).click();
      await page.waitForLoadState("networkidle");

      // Click on Skills Analytics tab
      await page.getByRole("tab", { name: /skills analytics/i }).click();

      // Check key metrics cards are displayed
      await expect(page.getByText("Total Skills")).toBeVisible();
      await expect(page.getByText("150")).toBeVisible();

      await expect(page.getByText("Coverage")).toBeVisible();
      await expect(page.getByText("80.0%")).toBeVisible();

      await expect(page.getByText("Avg Confidence")).toBeVisible();
      await expect(page.getByText("82.5%")).toBeVisible();

      // Check top skills chart title
      await expect(page.getByText("Top 15 Skills")).toBeVisible();

      // Check skills by type chart title
      await expect(page.getByText("Skills by Type")).toBeVisible();

      // Check skills inventory table
      await expect(page.getByText("Skills Inventory")).toBeVisible();
      await expect(page.getByText("Python")).toBeVisible();
      await expect(page.getByText("Project Management")).toBeVisible();
      await expect(page.getByText("92.0%")).toBeVisible(); // Avg confidence
    });

    test("should handle empty skills data", async ({ page }) => {
      // Mock empty stats
      await page.route("**/api/analytics/skills/stats", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            total_unique_skills: 0,
            total_skill_associations: 0,
            jobs_with_skills: 0,
            total_jobs: 150,
            skills_coverage_percentage: 0.0,
            avg_skills_per_job: 0.0,
            avg_confidence_score: 0.0,
          }),
        });
      });

      await page.route("**/api/analytics/skills/top?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ total_jobs: 150, top_skills: [] }),
        });
      });

      await page.route("**/api/analytics/skills/types", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ skill_types: [], total_types: 0 }),
        });
      });

      await page.route("**/api/analytics/skills/inventory?**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ skills: [], total: 0, limit: 20, offset: 0 }),
        });
      });

      await page.getByRole("button", { name: /dashboard/i }).click();
      await page.waitForLoadState("networkidle");
      await page.getByRole("tab", { name: /skills analytics/i }).click();

      // Should show "0" for metrics
      await expect(page.getByText("Total Skills")).toBeVisible();
      await expect(page.locator('text="0"').first()).toBeVisible();

      // Should show "No data" messages
      await expect(page.getByText(/no skills data available/i)).toBeVisible();
    });
  });

  test.describe("Skills Filtering in Jobs List", () => {
    test("should filter jobs by selected skills", async ({ page }) => {
      // Navigate to jobs list
      await page.getByRole("button", { name: /jobs/i }).click();
      await page.waitForLoadState("networkidle");

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
      await page.getByRole("button", { name: /jobs/i }).click();
      await page.waitForLoadState("networkidle");

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
      await page.getByRole("button", { name: /jobs/i }).click();
      await page.waitForLoadState("networkidle");

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
      await page.getByRole("button", { name: /jobs/i }).click();
      await page.waitForLoadState("networkidle");

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
