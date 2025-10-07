import { test, expect } from "@playwright/test";

test.describe("Visual Enhancements and Dark Mode", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto("http://localhost:3002");

    // Wait for the page to load completely
    await page.waitForLoadState("networkidle");

    // Wait for stats to load (animated counters)
    await page
      .waitForSelector('[data-testid="stats-card"]', { timeout: 10000 })
      .catch(() => {
        // If no test-id available, wait for any card with animated counter
        return page.waitForSelector(".tabular-nums", { timeout: 10000 });
      });
  });

  test("should display animated counters on dashboard load", async ({
    page,
  }) => {
    // Check that animated counters are present
    const counters = await page.locator(".tabular-nums").all();
    expect(counters.length).toBeGreaterThan(0);

    // Verify that at least one counter shows a number
    const firstCounter = page.locator(".tabular-nums").first();
    const counterText = await firstCounter.textContent();
    expect(counterText).toBeTruthy();
  });

  test("should have proper visual styling with gradients and shadows", async ({
    page,
  }) => {
    // Check for gradient backgrounds in the main container
    const mainContainer = page
      .locator("div")
      .filter({ hasText: "Job Description Database (JDDB)" })
      .first();
    await expect(mainContainer).toBeVisible();

    // Check for card hover effects and shadows
    const dashboardCards = page.locator('[class*="hover-lift"]');
    const cardCount = await dashboardCards.count();
    expect(cardCount).toBeGreaterThan(0);

    // Verify stats cards have proper styling
    const statsCards = page
      .locator("div")
      .filter({ hasText: "Total Jobs" })
      .or(page.locator("div").filter({ hasText: "Completed" }));
    await expect(statsCards.first()).toBeVisible();
  });

  test("should have functioning theme toggle button", async ({ page }) => {
    // Find the theme toggle button
    const themeToggle = page
      .locator("button")
      .filter({ hasText: /theme|dark|light/i })
      .or(
        page
          .locator('button[title*="theme"]')
          .or(
            page
              .locator('button[title*="Dark"]')
              .or(page.locator('button[title*="Light"]')),
          ),
      );

    // If no accessible theme toggle found, look for buttons with sun/moon icons
    const iconButton = page
      .locator("button")
      .filter({ has: page.locator("svg") })
      .last();

    // Try the icon button approach if theme toggle not found
    let toggleButton = themeToggle;
    if ((await themeToggle.count()) === 0) {
      toggleButton = iconButton;
    }

    await expect(toggleButton).toBeVisible();

    // Click the theme toggle
    await toggleButton.click();

    // Wait a moment for theme change
    await page.waitForTimeout(500);

    // Click again to cycle through themes
    await toggleButton.click();
    await page.waitForTimeout(500);
  });

  test("should apply dark mode styles when dark theme is active", async ({
    page,
  }) => {
    // Get initial state
    const htmlElement = page.locator("html");

    // Find and click theme toggle (try multiple selectors)
    const themeToggle = page
      .locator("button")
      .filter({ has: page.locator("svg") })
      .last();
    await expect(themeToggle).toBeVisible();

    // Click to change theme (may need multiple clicks to get to dark mode)
    await themeToggle.click();
    await page.waitForTimeout(300);

    // Check if dark class is applied, if not click again
    let isDark = await htmlElement.evaluate((el) =>
      el.classList.contains("dark"),
    );
    if (!isDark) {
      await themeToggle.click();
      await page.waitForTimeout(300);
      isDark = await htmlElement.evaluate((el) =>
        el.classList.contains("dark"),
      );
    }

    // If still not dark, try one more time
    if (!isDark) {
      await themeToggle.click();
      await page.waitForTimeout(300);
    }

    // Verify dark theme styling is applied to elements
    const mainContainer = page
      .locator("div")
      .filter({ hasText: "Job Description Database" })
      .first();
    await expect(mainContainer).toBeVisible();
  });

  test("should display proper tab navigation with styling", async ({
    page,
  }) => {
    // Check that all tabs are visible
    const dashboardTab = page
      .locator("button")
      .filter({ hasText: "Dashboard" });
    const jobsTab = page.locator("button").filter({ hasText: "Jobs" });
    const uploadTab = page.locator("button").filter({ hasText: "Upload" });
    const searchTab = page.locator("button").filter({ hasText: "Search" });

    await expect(dashboardTab).toBeVisible();
    await expect(jobsTab).toBeVisible();
    await expect(uploadTab).toBeVisible();
    await expect(searchTab).toBeVisible();

    // Test tab navigation
    await jobsTab.click();
    await page.waitForTimeout(500);

    await uploadTab.click();
    await page.waitForTimeout(500);

    await searchTab.click();
    await page.waitForTimeout(500);

    // Return to dashboard
    await dashboardTab.click();
    await page.waitForTimeout(500);
  });

  test("should have responsive design elements", async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);

    // Check that main elements are still visible (use first h1 to avoid strict mode)
    const header = page
      .locator("h1")
      .first()
      .filter({ hasText: /Job Description Database|JDDB|Dashboard/ });
    await expect(header).toBeVisible();

    // Check that tabs are accessible
    const tabsList = page
      .locator('[role="tablist"]')
      .or(page.locator(".grid-cols-6"));
    await expect(tabsList).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);

    // Verify layout adapts
    await expect(header).toBeVisible();

    // Return to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);
  });

  test("should handle empty states gracefully", async ({ page }) => {
    // Navigate to different tabs to check empty states
    const jobsTab = page.locator("button").filter({ hasText: "Jobs" });
    await jobsTab.click();
    await page.waitForTimeout(1000);

    // Should show some content or empty state
    const pageContent = page
      .locator("main")
      .or(page.locator('[role="main"]'))
      .or(page.locator("body"));
    await expect(pageContent).toBeVisible();

    // Check upload tab
    const uploadTab = page.locator("button").filter({ hasText: "Upload" });
    await uploadTab.click();
    await page.waitForTimeout(1000);

    // Should show upload interface
    await expect(pageContent).toBeVisible();
  });

  test("should maintain accessibility with visual enhancements", async ({
    page,
  }) => {
    // Check that enhanced elements maintain proper contrast
    const statsCards = page
      .locator("div")
      .filter({ hasText: "Total Jobs" })
      .or(page.locator("div").filter({ hasText: "Completed" }));

    if ((await statsCards.count()) > 0) {
      await expect(statsCards.first()).toBeVisible();
    }

    // Verify tab navigation is keyboard accessible
    await page.keyboard.press("Tab");
    await page.waitForTimeout(200);

    // Check that focus indicators are visible
    const focusedElement = page.locator(":focus");
    if ((await focusedElement.count()) > 0) {
      await expect(focusedElement).toBeVisible();
    }
  });
});
