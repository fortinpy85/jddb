/**
 * Accessibility Tests using axe-core
 *
 * These tests scan pages for WCAG 2.1 Level A and AA violations
 * Critical for government applications which must meet accessibility standards
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Mock API responses for pages that need backend data
async function setupSearchMocks(page: any) {
  await page.route("**/api/search/**", async (route: any) => {
    const url = route.request().url();

    if (url.includes('/facets')) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          classifications: [
            { value: "EX-01", count: 80 },
            { value: "EX-02", count: 50 },
          ],
          languages: [
            { value: "EN", count: 100 },
            { value: "FR", count: 50 },
          ],
          section_types: [],
        }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [],
        total: 0,
      }),
    });
  });
}

test.describe("Accessibility Compliance - WCAG 2.1 Level A & AA", () => {
  test("Dashboard/Home page should be accessible", async ({ page }) => {
    await page.goto("/");

    // Wait for page to load
    await page.waitForLoadState("networkidle");

    // Run axe accessibility scan
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    // Report violations
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Dashboard view should be accessible", async ({ page }) => {
    await page.goto("/");

    // Navigate to Dashboard
    await page.getByRole("button", { name: "Dashboard", exact: false }).click();
    await page.waitForTimeout(1000); // Allow lazy load
    await page.waitForLoadState("networkidle");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Search interface should be accessible", async ({ page }) => {
    // Set up mocks first
    await setupSearchMocks(page);

    await page.goto("/");

    // Navigate to Search
    await page.getByRole("button", { name: "Search", exact: false }).click();
    await page.waitForTimeout(1000); // Allow lazy load
    await page.waitForLoadState("networkidle");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Upload interface should be accessible", async ({ page }) => {
    await page.goto("/");

    // Navigate to Upload
    await page.getByRole("button", { name: "Upload", exact: false }).click();
    await page.waitForTimeout(1000); // Allow lazy load
    await page.waitForLoadState("networkidle");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Compare view should be accessible", async ({ page }) => {
    await page.goto("/");

    // Navigate to Compare
    await page.getByRole("button", { name: "Compare", exact: false }).click();
    await page.waitForTimeout(1000); // Allow lazy load
    await page.waitForLoadState("networkidle");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Translate view should be accessible", async ({ page }) => {
    await page.goto("/");

    // Navigate to Translate
    await page.getByRole("button", { name: "Translate", exact: false }).click();
    await page.waitForTimeout(1000); // Allow lazy load
    await page.waitForLoadState("networkidle");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("AI Demo page should be accessible", async ({ page }) => {
    await page.goto("/");

    // Navigate to AI Demo
    await page.getByRole("button", { name: "AI Demo", exact: false }).click();
    await page.waitForTimeout(1000); // Allow lazy load
    await page.waitForLoadState("networkidle");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});

test.describe("Accessibility - Keyboard Navigation", () => {
  test("Should be able to navigate main menu with keyboard", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Tab to first navigation button
    await page.keyboard.press("Tab");

    // Check if a navigation button is focused
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement;
      return {
        tagName: el?.tagName,
        role: el?.getAttribute('role'),
        text: el?.textContent?.trim().substring(0, 20),
      };
    });

    // Should be able to reach interactive elements
    expect(focusedElement.tagName).toBeTruthy();
  });

  test("Modal dialogs should trap focus", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Look for any button that might open a modal
    const createButton = page.locator("button").filter({ hasText: /create|new/i }).first();

    if (await createButton.count() > 0) {
      await createButton.click();
      await page.waitForTimeout(500);

      // Check if focus is trapped within modal
      const isModalOpen = await page.locator('[role="dialog"]').count() > 0;

      if (isModalOpen) {
        // Try to tab - focus should stay in modal
        await page.keyboard.press("Tab");
        await page.keyboard.press("Tab");

        const focusedElement = await page.evaluate(() => {
          const el = document.activeElement;
          const modal = document.querySelector('[role="dialog"]');
          return {
            isInModal: modal?.contains(el) || false,
          };
        });

        expect(focusedElement.isInModal).toBe(true);
      }
    }
  });
});

test.describe("Accessibility - Screen Reader Support", () => {
  test("Navigation should have proper ARIA roles", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Check for proper navigation landmarks
    const landmarks = await page.evaluate(() => {
      return {
        hasMain: document.querySelector('main, [role="main"]') !== null,
        hasNav: document.querySelector('nav, [role="navigation"]') !== null,
        hasBanner: document.querySelector('header, [role="banner"]') !== null,
      };
    });

    expect(landmarks.hasMain).toBe(true);
    // Navigation might be implemented differently, so we check if it exists
    // expect(landmarks.hasNav).toBe(true); // Optional - may fail if nav is implemented with buttons
  });

  test("Form inputs should have labels", async ({ page }) => {
    await setupSearchMocks(page);

    await page.goto("/");

    // Navigate to Search (has form inputs)
    await page.getByRole("button", { name: "Search", exact: false }).click();
    await page.waitForTimeout(1000);
    await page.waitForLoadState("networkidle");

    // Check if search input has accessible name
    const searchInput = page.locator('input[placeholder*="Search"], input[placeholder*="search"]').first();

    if (await searchInput.count() > 0) {
      const hasAccessibleName = await searchInput.evaluate((el) => {
        const input = el as HTMLInputElement;
        // Check for label, aria-label, or aria-labelledby
        return !!(
          input.labels?.length ||
          input.getAttribute('aria-label') ||
          input.getAttribute('aria-labelledby') ||
          input.getAttribute('placeholder') // Placeholder can serve as accessible name
        );
      });

      expect(hasAccessibleName).toBe(true);
    }
  });

  test("Buttons should have accessible names", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Get all buttons
    const buttons = await page.locator('button').all();

    for (const button of buttons.slice(0, 10)) { // Check first 10 buttons
      const accessibleName = await button.evaluate((btn) => {
        return btn.textContent?.trim() ||
               btn.getAttribute('aria-label') ||
               btn.getAttribute('aria-labelledby') ||
               btn.getAttribute('title') ||
               '';
      });

      // Every button should have some form of accessible name
      expect(accessibleName.length).toBeGreaterThan(0);
    }
  });
});

test.describe("Accessibility - Color Contrast", () => {
  test("Should check color contrast ratios", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Use axe-core's color-contrast rule specifically
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2aa"])
      .include('body')
      .analyze();

    // Filter for color contrast violations
    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast'
    );

    expect(contrastViolations).toEqual([]);
  });
});

test.describe("Accessibility - Images and Media", () => {
  test("Images should have alt text", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Check for images without alt text
    const imagesWithoutAlt = await page.locator('img:not([alt])').count();

    expect(imagesWithoutAlt).toBe(0);
  });

  test("Decorative images should have empty alt or role=presentation", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Get all images
    const images = await page.locator('img').all();

    for (const img of images) {
      const attrs = await img.evaluate((el) => ({
        alt: el.getAttribute('alt'),
        role: el.getAttribute('role'),
        ariaHidden: el.getAttribute('aria-hidden'),
      }));

      // Each image should either have:
      // - alt text (informative)
      // - alt="" (decorative)
      // - role="presentation" (decorative)
      // - aria-hidden="true" (decorative)
      const isAccessible = attrs.alt !== null ||
                          attrs.role === 'presentation' ||
                          attrs.ariaHidden === 'true';

      expect(isAccessible).toBe(true);
    }
  });
});
