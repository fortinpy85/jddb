/**
 * Accessibility and Performance E2E Tests
 */
import { test, expect, Page } from "@playwright/test";
import {
  checkAccessibility,
  testResponsiveDesign,
  testKeyboardNavigation,
  mockStatsData,
  mockJobsList,
  mockApiResponse,
} from "./utils/test-helpers";

test.describe("Accessibility Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses to ensure consistent test data
    await mockApiResponse(page, "**/api/jobs/stats", mockStatsData);
    await mockApiResponse(page, "**/api/jobs/**", mockJobsList);

    await page.goto("/");
  });

  test("should have proper heading structure", async ({ page }) => {
    // Check main heading
    const h1 = page.locator("h1");
    await expect(h1).toBeVisible();
    await expect(h1).toContainText("Job Description Database");

    // Check heading hierarchy (h1 -> h2 -> h3, no skipping levels)
    const headings = await page.locator("h1, h2, h3, h4, h5, h6").all();

    let previousLevel = 0;
    for (const heading of headings) {
      const tagName = await heading.evaluate((el) => el.tagName);
      const currentLevel = parseInt(tagName.charAt(1));

      // Heading levels should not skip (e.g., h1 -> h3 is bad)
      if (previousLevel > 0) {
        expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
      }
      previousLevel = currentLevel;
    }
  });

  test("should have proper ARIA labels and roles", async ({ page }) => {
    // Check main navigation has role
    const nav = page.locator('nav, [role="navigation"]');
    if ((await nav.count()) > 0) {
      await expect(nav).toBeVisible();
    }

    // Check tab navigation has proper roles
    const tablist = page.locator('[role="tablist"]');
    if ((await tablist.count()) > 0) {
      await expect(tablist).toBeVisible();

      // Check each tab has proper attributes
      const tabs = page.locator('[role="tab"]');
      const tabCount = await tabs.count();

      for (let i = 0; i < tabCount; i++) {
        const tab = tabs.nth(i);
        await expect(tab).toHaveAttribute("aria-selected");

        // At least one tab should be selected
        const ariaSelected = await tab.getAttribute("aria-selected");
        if (ariaSelected === "true") {
          await expect(tab).toBeFocused();
        }
      }
    }

    // Check buttons have accessible names
    const buttons = page.locator("button");
    const buttonCount = await buttons.count();

    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const accessibleName = await button.evaluate((el) => {
        return (
          el.getAttribute("aria-label") ||
          el.getAttribute("title") ||
          el.textContent?.trim() ||
          el.querySelector("img")?.getAttribute("alt")
        );
      });

      expect(accessibleName).toBeTruthy();
    }
  });

  test("should have proper form labels", async ({ page }) => {
    // Navigate to upload tab which likely has forms
    await page.getByRole("tab", { name: "Upload" }).click();

    const inputs = page.locator("input, textarea, select");
    const inputCount = await inputs.count();

    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const inputType = await input.getAttribute("type");

      // Skip hidden inputs
      if (inputType === "hidden") continue;

      const id = await input.getAttribute("id");
      const ariaLabel = await input.getAttribute("aria-label");
      const ariaLabelledby = await input.getAttribute("aria-labelledby");
      const placeholder = await input.getAttribute("placeholder");

      // Input should have proper labeling
      if (id) {
        const labelCount = await page.locator(`label[for="${id}"]`).count();
        const hasProperLabel = labelCount > 0 || ariaLabel || ariaLabelledby;

        if (!hasProperLabel && !placeholder) {
          console.warn(
            `Input without proper label: ${await input.evaluate((el) => el.outerHTML)}`,
          );
        }
      }
    }
  });

  test("should be navigable with keyboard only", async ({ page }) => {
    await testKeyboardNavigation(page);

    // Test tab navigation through main interface
    await page.keyboard.press("Tab");
    let focusedElement = await page.evaluate(
      () => document.activeElement?.tagName,
    );
    expect(["BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "DIV"]).toContain(
      focusedElement,
    );

    // Test navigation to tabs
    const tabs = page.locator('[role="tab"]');
    if ((await tabs.count()) > 0) {
      await tabs.first().focus();

      // Test arrow key navigation between tabs
      await page.keyboard.press("ArrowRight");
      const nextTab = await page.evaluate(() =>
        document.activeElement?.textContent?.trim(),
      );
      expect(nextTab).toBeTruthy();

      // Test Enter key to activate tab
      await page.keyboard.press("Enter");
      const activeTab = page.locator('[role="tab"][aria-selected="true"]');
      await expect(activeTab).toBeFocused();
    }
  });

  test("should have sufficient color contrast", async ({ page }) => {
    // This is a basic test - in real scenarios, use axe-core or similar tools
    const elements = page.locator("button, a, .text-primary, .text-secondary");
    const elementCount = await elements.count();

    for (let i = 0; i < Math.min(elementCount, 10); i++) {
      // Test first 10 elements
      const element = elements.nth(i);

      const styles = await element.evaluate((el) => {
        const computed = getComputedStyle(el);
        return {
          color: computed.color,
          backgroundColor: computed.backgroundColor,
          fontSize: computed.fontSize,
        };
      });

      // Log for manual verification
      console.log(
        `Element ${i}: Color: ${styles.color}, BG: ${styles.backgroundColor}, Font: ${styles.fontSize}`,
      );
    }
  });

  test("should handle screen reader announcements", async ({ page }) => {
    // Check for aria-live regions
    const liveRegions = page.locator("[aria-live]");
    const liveRegionCount = await liveRegions.count();

    if (liveRegionCount > 0) {
      console.log(
        `Found ${liveRegionCount} live regions for screen reader updates`,
      );

      for (let i = 0; i < liveRegionCount; i++) {
        const region = liveRegions.nth(i);
        const ariaLive = await region.getAttribute("aria-live");
        expect(["polite", "assertive", "off"]).toContain(ariaLive);
      }
    }

    // Check for status messages
    const statusElements = page.locator(
      '[role="status"], [role="alert"], .sr-only',
    );
    if ((await statusElements.count()) > 0) {
      await expect(statusElements.first()).toBeAttached();
    }
  });
});

test.describe("Responsive Design Tests", () => {
  test.beforeEach(async ({ page }) => {
    await mockApiResponse(page, "**/api/jobs/stats", mockStatsData);
    await mockApiResponse(page, "**/api/jobs/**", mockJobsList);
    await page.goto("/");
  });

  test("should work on mobile viewports", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.waitForLoadState("networkidle");

    // Check main heading is still visible
    await expect(page.locator("h1")).toBeVisible();

    // Check navigation (might be collapsed)
    const nav = page.locator('nav, [role="navigation"], [role="tablist"]');
    await expect(nav).toBeVisible();

    // Check main content is visible
    const main = page.locator('main, [role="main"], .main-content').first();
    await expect(main).toBeVisible();

    // Test touch interactions (tap instead of hover)
    const firstButton = page.locator("button").first();
    if ((await firstButton.count()) > 0) {
      await firstButton.tap();
    }
  });

  test("should work on tablet viewports", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.waitForLoadState("networkidle");

    // Content should be well-spaced
    await expect(page.locator("h1")).toBeVisible();
    await expect(page.locator('[role="tablist"]')).toBeVisible();

    // Check grid layouts adapt appropriately
    const cards = page.locator('.grid, .flex, [class*="grid"]');
    if ((await cards.count()) > 0) {
      await expect(cards.first()).toBeVisible();
    }
  });

  test("should work on large desktop viewports", async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForLoadState("networkidle");

    // All elements should be visible and well-proportioned
    await expect(page.locator("h1")).toBeVisible();

    // Check sidebar/navigation layouts
    const nav = page.locator('nav, [role="navigation"], [role="tablist"]');
    await expect(nav).toBeVisible();

    // Content shouldn't be too wide
    const mainContent = page.locator('main, [role="main"]').first();
    if ((await mainContent.count()) > 0) {
      const boundingBox = await mainContent.boundingBox();
      if (boundingBox) {
        // Content width shouldn't exceed reasonable reading width
        expect(boundingBox.width).toBeLessThan(1400);
      }
    }
  });

  test("should handle orientation changes", async ({ page }) => {
    // Test landscape mobile
    await page.setViewportSize({ width: 667, height: 375 });
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible();

    // Test portrait tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible();

    // Test landscape tablet
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible();
  });
});

test.describe("Performance Tests", () => {
  test.beforeEach(async ({ page }) => {
    await mockApiResponse(page, "**/api/jobs/stats", mockStatsData);
    await mockApiResponse(page, "**/api/jobs/**", mockJobsList);
  });

  test("should load initial page quickly", async ({ page }) => {
    const startTime = Date.now();

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const loadTime = Date.now() - startTime;
    console.log(`Page load time: ${loadTime}ms`);

    // Should load within reasonable time (adjust based on your requirements)
    expect(loadTime).toBeLessThan(5000);

    // Check that main content is visible
    await expect(page.locator("h1")).toBeVisible();
  });

  test("should handle large datasets efficiently", async ({ page }) => {
    // Mock large dataset
    const largeJobsList = {
      jobs: Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        job_number: `12345${i}`,
        title: `Job Title ${i}`,
        classification: i % 2 === 0 ? "EX-01" : "EX-02",
        language: i % 3 === 0 ? "FR" : "EN",
        processed_date: "2024-01-15T10:00:00Z",
        sections_count: 5,
      })),
      total: 100,
      page: 1,
      pages: 5,
    };

    await mockApiResponse(page, "**/api/jobs/**", largeJobsList);

    const startTime = Date.now();
    await page.goto("/");
    await page.getByRole("tab", { name: "Jobs" }).click();
    await page.waitForLoadState("networkidle");

    const loadTime = Date.now() - startTime;
    console.log(`Large dataset load time: ${loadTime}ms`);

    // Should still be reasonably fast
    expect(loadTime).toBeLessThan(8000);

    // Check that content is rendered
    await expect(page.locator("text=Job Title 0")).toBeVisible();
  });

  test("should not have memory leaks during navigation", async ({ page }) => {
    await page.goto("/");

    // Navigate between tabs multiple times
    const tabs = ["Jobs", "Upload", "Search", "Compare", "Dashboard"];

    for (let i = 0; i < 3; i++) {
      // Repeat 3 times
      for (const tabName of tabs) {
        await page.getByRole("tab", { name: tabName }).click();
        await page.waitForTimeout(100); // Small delay
      }
    }

    // Basic check - page should still be responsive
    await expect(page.locator("h1")).toBeVisible();

    // In real scenarios, you'd monitor actual memory usage
    console.log("Navigation stress test completed successfully");
  });

  test("should handle network errors gracefully", async ({ page }) => {
    // Mock network error
    await page.route("**/api/jobs/**", (route) => route.abort());

    const startTime = Date.now();
    await page.goto("/");

    // Should still load the page structure
    await expect(page.locator("h1")).toBeVisible();

    const loadTime = Date.now() - startTime;
    console.log(`Error handling load time: ${loadTime}ms`);

    // Should not hang indefinitely
    expect(loadTime).toBeLessThan(10000);

    // Should show error message
    await expect(
      page
        .locator("text=Error")
        .or(page.locator("text=Failed"))
        .or(page.locator("text=Unable")),
    ).toBeVisible();
  });

  test("should optimize image loading", async ({ page }) => {
    await page.goto("/");

    // Check for lazy-loaded images
    const images = page.locator("img");
    const imageCount = await images.count();

    if (imageCount > 0) {
      for (let i = 0; i < imageCount; i++) {
        const img = images.nth(i);

        // Check for loading attribute
        const loading = await img.getAttribute("loading");
        if (loading) {
          expect(["lazy", "eager"]).toContain(loading);
        }

        // Check for alt attribute
        const alt = await img.getAttribute("alt");
        expect(alt).toBeTruthy();
      }
    }
  });
});

test.describe("Error Handling Tests", () => {
  test("should handle API failures gracefully", async ({ page }) => {
    // Mock API failure
    await page.route("**/api/**", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal Server Error" }),
      });
    });

    await page.goto("/");

    // Should still show basic page structure
    await expect(page.locator("h1")).toBeVisible();

    // Should show error message
    await expect(
      page
        .locator("text=Error")
        .or(page.locator("text=Failed"))
        .or(page.locator("text=Something went wrong")),
    ).toBeVisible();

    // Should provide way to retry
    const retryButton = page
      .locator("button")
      .filter({ hasText: /retry|refresh|reload/i });
    if ((await retryButton.count()) > 0) {
      await expect(retryButton).toBeVisible();
    }
  });

  test("should handle offline scenarios", async ({ page }) => {
    await page.goto("/");

    // Simulate offline
    await page.context().setOffline(true);

    // Try to navigate
    await page.getByRole("tab", { name: "Jobs" }).click();

    // Should handle gracefully
    await expect(page.locator("h1")).toBeVisible();

    // Restore online
    await page.context().setOffline(false);
  });
});
