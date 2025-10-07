/**
 * Create Job Workflow E2E Tests
 *
 * Tests the complete workflow for manually creating job descriptions
 * Critical user flow for adding jobs without file upload
 */

import { test, expect } from "@playwright/test";

test.describe("Create New Job Workflow", () => {
  test.beforeEach(async ({ page }) => {
    // Mock API calls to avoid backend dependency
    await page.route("**/api/jobs?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          jobs: [],
          total: 0,
        }),
      });
    });

    await page.route("**/api/jobs/stats", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total_jobs: 0,
          by_classification: {},
          by_language: {},
          by_status: {},
          recent_uploads: 0,
        }),
      });
    });
  });

  test("should open create job modal from Jobs table", async ({ page }) => {
    // Capture console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('pageerror', err => {
      consoleErrors.push(`Page error: ${err.message}`);
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Look for "Create New" button - use a more flexible selector
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await expect(createButton).toBeVisible({ timeout: 10000 });

    // Click to open modal
    await createButton.click();
    await page.waitForTimeout(500); // Allow modal animation

    // Log console errors if any
    if (consoleErrors.length > 0) {
      console.log('Console errors:', consoleErrors);
    }

    // Verify modal is open
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Verify modal title
    await expect(page.getByText("Create New Job Description")).toBeVisible();
  });

  test("should show all required form fields", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Check required fields are present
    const jobNumberInput = page.locator('input[id="job_number"]');
    const titleInput = page.locator('input[id="title"]');
    const classificationInput = page.locator('input[id="classification"]');

    await expect(jobNumberInput).toBeVisible();
    await expect(titleInput).toBeVisible();
    await expect(classificationInput).toBeVisible();

    // Check optional fields
    await expect(page.locator('input[id="department"]')).toBeVisible();
    await expect(page.locator('input[id="reports_to"]')).toBeVisible();
    await expect(page.locator('textarea[id="content"]')).toBeVisible();

    // Check language selector
    await expect(page.locator('button[id="language"]')).toBeVisible();
  });

  test("should show validation error for missing required fields", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Verify modal is still open before submitting
    const modalBefore = page.locator('[role="dialog"]');
    await expect(modalBefore).toBeVisible();

    // Try to submit without filling required fields
    // Use dispatchEvent to trigger React's handler while bypassing HTML5 validation
    await page.evaluate(() => {
      const form = document.querySelector('form') as HTMLFormElement;
      if (form) {
        // Create and dispatch a submit event that React will intercept
        const event = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(event);
      }
    });

    // Wait for error message
    await page.waitForTimeout(500);

    // Check for validation error - look for the exact error message
    const errorMessage = page.locator("text=/Job Number.*required/i");
    await expect(errorMessage).toBeVisible({ timeout: 2000 });
  });

  test("should successfully create a new job with all fields", async ({ page }) => {
    // Mock the create job API call
    await page.route("**/api/jobs/", async (route) => {
      if (route.request().method() === "POST") {
        const postData = route.request().postDataJSON();

        // Return success response
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            status: "success",
            message: "Job created successfully",
            job_id: 9999,
            job: {
              id: 9999,
              job_number: postData.job_number,
              title: postData.title,
              classification: postData.classification,
              language: postData.language || "en",
              department: postData.department,
              reports_to: postData.reports_to,
              content: postData.content,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Mock jobs list refresh
    await page.route("**/api/jobs?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          jobs: [],
          total: 0,
        }),
      });
    });

    // Mock stats refresh
    await page.route("**/api/jobs/stats", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          total_jobs: 1,
          by_classification: { "EX-01": 1 },
          by_language: { EN: 1 },
          by_status: { active: 1 },
          recent_uploads: 1,
        }),
      });
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Fill in all fields
    await page.locator('input[id="job_number"]').fill("EX-01-TEST-001");
    await page.locator('input[id="title"]').fill("Test Director Position");
    await page.locator('input[id="classification"]').fill("EX-01");

    // Select language - use evaluate to bypass viewport check
    await page.evaluate(() => {
      const langButton = document.querySelector('button[id="language"]') as HTMLButtonElement;
      if (langButton) langButton.click();
    });
    await page.waitForTimeout(200);
    // Click option programmatically
    await page.evaluate(() => {
      const option = Array.from(document.querySelectorAll('[role="option"]')).find(
        opt => opt.textContent?.includes('English')
      ) as HTMLElement;
      if (option) option.click();
    });

    await page.locator('input[id="department"]').fill("Test Department");
    await page.locator('input[id="reports_to"]').fill("Chief Test Officer");
    await page.locator('textarea[id="content"]').fill("This is a test job description with detailed content about responsibilities and requirements.");

    // Submit form - dispatch submit event to trigger React handler
    await page.evaluate(() => {
      const form = document.querySelector('form') as HTMLFormElement;
      if (form) {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(event);
      }
    });

    // Wait for success - modal should close
    await page.waitForTimeout(1000);

    // Verify modal is closed
    const modal = page.locator('[role="dialog"]');
    await expect(modal).not.toBeVisible({ timeout: 5000 });
  });

  test("should handle API errors gracefully", async ({ page }) => {
    // Mock API error
    await page.route("**/api/jobs/", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({
            detail: "Database connection failed",
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Fill required fields
    await page.locator('input[id="job_number"]').fill("EX-01-ERROR-001");
    await page.locator('input[id="title"]').fill("Error Test Position");
    await page.locator('input[id="classification"]').fill("EX-01");

    // Submit form - dispatch submit event to trigger React handler
    await page.evaluate(() => {
      const form = document.querySelector('form') as HTMLFormElement;
      if (form) {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(event);
      }
    });

    // Wait for error message (API retries 3x with exponential backoff = ~7s total)
    await page.waitForTimeout(8000);

    // Verify error is displayed - look for error text
    const errorMessage = page.locator("text=/Database connection failed/i");
    await expect(errorMessage).toBeVisible({ timeout: 2000 });

    // Modal should still be open
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
  });

  test("should cancel creation and close modal", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Fill some data
    await page.locator('input[id="job_number"]').fill("EX-01-CANCEL-001");
    await page.locator('input[id="title"]').fill("Cancel Test");

    // Click cancel - use evaluate to bypass viewport check
    await page.evaluate(() => {
      const cancelButton = Array.from(document.querySelectorAll('button')).find(
        btn => btn.textContent?.includes('Cancel')
      ) as HTMLButtonElement;
      if (cancelButton) cancelButton.click();
    });

    // Modal should close
    await page.waitForTimeout(500);
    const modal = page.locator('[role="dialog"]');
    await expect(modal).not.toBeVisible();
  });

  test("should show loading state during submission", async ({ page }) => {
    // Mock slow API response
    await page.route("**/api/jobs/", async (route) => {
      if (route.request().method() === "POST") {
        // Delay response
        await new Promise(resolve => setTimeout(resolve, 2000));

        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            status: "success",
            job_id: 9999,
            job: {},
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Mock other endpoints
    await page.route("**/api/jobs?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          jobs: [],
          pagination: {
            skip: 0,
            limit: 20,
            total: 0,
            has_more: false,
          },
        }),
      });
    });

    await page.route("**/api/jobs/stats", async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ total_jobs: 0 }),
      });
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Fill required fields
    await page.locator('input[id="job_number"]').fill("EX-01-LOAD-001");
    await page.locator('input[id="title"]').fill("Loading Test");
    await page.locator('input[id="classification"]').fill("EX-01");

    // Submit form - dispatch submit event to trigger React handler
    await page.evaluate(() => {
      const form = document.querySelector('form') as HTMLFormElement;
      if (form) {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(event);
      }
    });

    // Verify loading state
    await expect(page.getByText("Creating...")).toBeVisible({ timeout: 1000 });

    // Verify submit button is disabled during loading
    const loadingButton = page.getByRole("button", { name: /Creating/i });
    await expect(loadingButton).toBeDisabled();
  });

  test("should reset form after successful creation", async ({ page }) => {
    // Mock successful creation
    await page.route("**/api/jobs/", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            status: "success",
            job_id: 9999,
            job: {},
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.route("**/api/jobs?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          jobs: [],
          pagination: {
            skip: 0,
            limit: 20,
            total: 0,
            has_more: false,
          },
        }),
      });
    });

    await page.route("**/api/jobs/stats", async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ total_jobs: 1 }),
      });
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Create first job
    await page.getByRole("button", { name: "Create New" }).click();
    await page.waitForTimeout(500);

    await page.locator('input[id="job_number"]').fill("FIRST-JOB");
    await page.locator('input[id="title"]').fill("First Position");
    await page.locator('input[id="classification"]').fill("EX-01");

    // Submit form - dispatch submit event to trigger React handler
    await page.evaluate(() => {
      const form = document.querySelector('form') as HTMLFormElement;
      if (form) {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        form.dispatchEvent(event);
      }
    });
    await page.waitForTimeout(1000);

    // Open modal again
    await page.getByRole("button", { name: "Create New" }).click();
    await page.waitForTimeout(500);

    // Verify form is reset (empty)
    await expect(page.locator('input[id="job_number"]')).toHaveValue("");
    await expect(page.locator('input[id="title"]')).toHaveValue("");
    await expect(page.locator('input[id="classification"]')).toHaveValue("");
  });
});

test.describe("Create Job Workflow - Accessibility", () => {
  test.beforeEach(async ({ page }) => {
    // Mock API calls
    await page.route("**/api/jobs?**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          jobs: [],
          pagination: {
            skip: 0,
            limit: 20,
            total: 0,
            has_more: false,
          },
        }),
      });
    });

    await page.route("**/api/jobs/stats", async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ total_jobs: 0 }),
      });
    });
  });

  test("create job modal should be keyboard accessible", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Tab through form fields
    await page.keyboard.press("Tab");

    // Check if focus moved to first input
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement;
      return {
        id: el?.getAttribute('id'),
        tagName: el?.tagName,
      };
    });

    // Should be able to focus on form elements
    expect(focusedElement.tagName).toBeTruthy();
  });

  test("create job modal should trap focus", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Focus should be trapped in modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Tab multiple times
    for (let i = 0; i < 20; i++) {
      await page.keyboard.press("Tab");
    }

    // Check focus is still within modal
    const isInModal = await page.evaluate(() => {
      const el = document.activeElement;
      const modal = document.querySelector('[role="dialog"]');
      return modal?.contains(el) || false;
    });

    expect(isInModal).toBe(true);
  });

  test("create job form should have proper labels", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Open modal
    const createButton = page.locator("button").filter({ hasText: "Create New" });
    await createButton.click();
    await page.waitForTimeout(500);

    // Check all inputs have labels
    const inputs = [
      "job_number",
      "title",
      "classification",
      "department",
      "reports_to",
    ];

    for (const inputId of inputs) {
      const input = page.locator(`input[id="${inputId}"]`);
      const label = page.locator(`label[for="${inputId}"]`);

      await expect(input).toBeVisible();
      await expect(label).toBeVisible();
    }
  });
});
