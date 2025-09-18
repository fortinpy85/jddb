/**
 * Test utilities and helpers for E2E tests
 */
import { Page, expect } from "@playwright/test";

/**
 * Mock API response for tests
 */
export async function mockApiResponse(
  page: Page,
  endpoint: string,
  response: any,
  status: number = 200,
) {
  await page.route(endpoint, async (route) => {
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(response),
    });
  });
}

/**
 * Wait for API call to complete
 */
export async function waitForApiCall(
  page: Page,
  endpoint: string,
  timeout: number = 5000,
) {
  return page.waitForResponse(
    (response) =>
      response.url().includes(endpoint) && response.status() === 200,
    { timeout },
  );
}

/**
 * Mock job data for testing
 */
export const mockJobData = {
  id: 1,
  job_number: "123456",
  title: "Director, Business Analysis",
  classification: "EX-01",
  language: "EN",
  processed_date: "2024-01-15T10:00:00Z",
  sections_count: 5,
  sections: [
    {
      id: 1,
      section_type: "GENERAL_ACCOUNTABILITY",
      section_content: "General accountability content...",
      section_order: 1,
    },
    {
      id: 2,
      section_type: "SPECIFIC_ACCOUNTABILITIES",
      section_content: "Specific accountability content...",
      section_order: 2,
    },
  ],
  job_metadata: {
    reports_to: "Director General",
    department: "Strategic Planning",
    fte_count: 12,
    salary_budget: 230000,
  },
};

/**
 * Mock jobs list data
 */
export const mockJobsList = {
  jobs: [
    {
      id: 1,
      job_number: "123456",
      title: "Director, Business Analysis",
      classification: "EX-01",
      language: "EN",
      processed_date: "2024-01-15T10:00:00Z",
      sections_count: 5,
    },
    {
      id: 2,
      job_number: "789012",
      title: "Senior Analyst",
      classification: "EX-02",
      language: "FR",
      processed_date: "2024-01-16T11:00:00Z",
      sections_count: 3,
    },
  ],
  total: 2,
  page: 1,
  pages: 1,
};

/**
 * Mock search results
 */
export const mockSearchResults = {
  results: [
    {
      job_id: 1,
      title: "Director, Business Analysis",
      snippet: "Responsible for strategic business analysis...",
      score: 0.95,
    },
  ],
  total: 1,
  query: "director",
};

/**
 * Mock statistics data
 */
export const mockStatsData = {
  total_jobs: 150,
  completed: 120,
  processing: 25,
  need_review: 5,
  classification_distribution: {
    "EX-01": 80,
    "EX-02": 50,
    "EX-03": 20,
  },
  language_distribution: {
    EN: 100,
    FR: 50,
  },
};

/**
 * Fill file upload input
 */
export async function uploadTestFile(
  page: Page,
  filePath: string,
  fileName: string = "test-job.txt",
) {
  // Create a test file content
  const fileContent = `
Job Number: 123456
Title: Test Job Description
Classification: EX-01
Language: EN

General Accountability:
This is a test job description for automated testing purposes.

Specific Accountabilities:
- Test accountability 1
- Test accountability 2
- Test accountability 3
  `;

  // Create file input and upload
  const fileChooserPromise = page.waitForEvent("filechooser");
  await page.click('input[type="file"]', { force: true });
  const fileChooser = await fileChooserPromise;

  // Create a File object for testing
  const buffer = Buffer.from(fileContent);
  await fileChooser.setFiles({
    name: fileName,
    mimeType: "text/plain",
    buffer: buffer,
  });
}

/**
 * Wait for loading state to complete
 */
export async function waitForLoading(page: Page, timeout: number = 10000) {
  // Wait for any loading indicators to disappear
  await page.waitForFunction(
    () =>
      !document.querySelector(
        '[aria-label*="loading"], [data-testid*="loading"], .loading',
      ),
    { timeout },
  );
}

/**
 * Check accessibility of page elements
 */
export async function checkAccessibility(page: Page) {
  // Check for proper headings structure
  const headings = await page.locator("h1, h2, h3, h4, h5, h6").all();
  expect(headings.length).toBeGreaterThan(0);

  // Check for alt text on images
  const images = await page.locator("img").all();
  for (const image of images) {
    const alt = await image.getAttribute("alt");
    if (alt === null || alt.trim() === "") {
      console.warn("Image without alt text found");
    }
  }

  // Check for proper form labels
  const inputs = await page.locator("input, textarea, select").all();
  for (const input of inputs) {
    const id = await input.getAttribute("id");
    const ariaLabel = await input.getAttribute("aria-label");
    const ariaLabelledby = await input.getAttribute("aria-labelledby");

    if (id) {
      const label = await page.locator(`label[for="${id}"]`).count();
      if (label === 0 && !ariaLabel && !ariaLabelledby) {
        console.warn("Input without proper label found");
      }
    }
  }
}

/**
 * Test responsive design at different viewports
 */
export async function testResponsiveDesign(page: Page) {
  const viewports = [
    { width: 320, height: 568 }, // Mobile
    { width: 768, height: 1024 }, // Tablet
    { width: 1024, height: 768 }, // Desktop small
    { width: 1920, height: 1080 }, // Desktop large
  ];

  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    await page.waitForLoadState("networkidle");

    // Check that main content is visible
    await expect(
      page.locator('main, [role="main"], .main-content'),
    ).toBeVisible();

    // Check navigation is accessible (might be collapsed on mobile)
    const nav = page.locator('nav, [role="navigation"]');
    if ((await nav.count()) > 0) {
      await expect(nav).toBeVisible();
    }
  }
}

/**
 * Test keyboard navigation
 */
export async function testKeyboardNavigation(page: Page) {
  // Test Tab navigation
  await page.keyboard.press("Tab");
  const firstFocused = await page.evaluate(
    () => document.activeElement?.tagName,
  );
  expect(["BUTTON", "INPUT", "A", "SELECT", "TEXTAREA"]).toContain(
    firstFocused,
  );

  // Test Enter key on focusable elements
  const focusableElements = await page
    .locator("button, input, a, select, textarea")
    .all();
  if (focusableElements.length > 0) {
    await focusableElements[0].focus();
    await page.keyboard.press("Enter");
  }
}

/**
 * Mock error responses for testing error handling
 */
export async function mockErrorResponse(
  page: Page,
  endpoint: string,
  status: number = 500,
  message: string = "Internal Server Error",
) {
  await page.route(endpoint, async (route) => {
    await route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify({ error: message, detail: message }),
    });
  });
}
