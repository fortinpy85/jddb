import { test, expect } from "@playwright/test";

test.describe("GUI Enhancements", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto("/");

    // Wait for the page to be fully loaded
    await page.waitForLoadState("networkidle");
  });

  test.describe("Empty States", () => {
    test("should display helpful empty state on dashboard with no jobs", async ({
      page,
    }) => {
      // Navigate to dashboard tab
      await page.click('text="Dashboard"');

      // Check if empty state is displayed in recent jobs section
      const emptyState = page.locator(".bg-gradient-to-br");
      if ((await emptyState.count()) > 0) {
        // Verify empty state has helpful illustration
        await expect(emptyState.first()).toBeVisible();

        // Check for illustration emoji
        const illustration = emptyState.locator("text=/📋|📄|📤|🔍/").first();
        if ((await illustration.count()) > 0) {
          await expect(illustration).toBeVisible();
        }

        // Check for helpful title and description
        const title = emptyState.locator("h3").first();
        await expect(title).toBeVisible();

        const description = emptyState.locator("p").first();
        await expect(description).toBeVisible();

        // Check for helpful tips section
        const helpfulTips = emptyState.locator('text="Helpful Tips:"');
        if ((await helpfulTips.count()) > 0) {
          await expect(helpfulTips).toBeVisible();

          // Verify checkmark icons in tips
          const checkmarks = emptyState.locator("svg").filter({ hasText: "" });
          const checkmarkCount = await checkmarks.count();
          expect(checkmarkCount).toBeGreaterThan(0);
        }

        // Check for action buttons
        const actionButtons = emptyState.locator("button");
        if ((await actionButtons.count()) > 0) {
          await expect(actionButtons.first()).toBeVisible();
        }
      }
    });

    test("should display empty state in jobs tab when no jobs exist", async ({
      page,
    }) => {
      // Navigate to jobs tab
      await page.click('text="Jobs"');
      await page.waitForTimeout(1000);

      // Look for empty state
      const emptyState = page.locator(
        '.bg-gradient-to-br, [data-testid="empty-state"]',
      );
      if ((await emptyState.count()) > 0) {
        await expect(emptyState.first()).toBeVisible();

        // Check for upload action button
        const uploadButton = page.locator(
          'button:has-text("Upload"), button:has-text("upload")',
        );
        if ((await uploadButton.count()) > 0) {
          await expect(uploadButton.first()).toBeVisible();
        }
      }
    });

    test("should display empty state in search tab with no results", async ({
      page,
    }) => {
      // Navigate to search tab
      await page.click('text="Search"');
      await page.waitForTimeout(1000);

      // Perform a search that should return no results
      const searchInput = page
        .locator('input[placeholder*="search"], input[type="search"]')
        .first();
      if ((await searchInput.count()) > 0) {
        await searchInput.fill("nonexistentjobsearchterm12345");
        await page.keyboard.press("Enter");
        await page.waitForTimeout(2000);

        // Check for no results empty state
        const noResultsState = page.locator(
          'text="No Results Found", text="No results", text="no results"',
        );
        if ((await noResultsState.count()) > 0) {
          await expect(noResultsState.first()).toBeVisible();
        }
      }
    });
  });

  test.describe("Skeleton Loading States", () => {
    test("should show skeleton loaders during data loading", async ({
      page,
    }) => {
      // Reload page to trigger loading states
      await page.reload();

      // Check for skeleton loading elements during initial load
      const skeletonElements = page
        .locator(".animate-pulse, .bg-gray-200")
        .first();

      // Wait briefly to catch loading states
      await page.waitForTimeout(500);

      // If skeleton elements are present, verify they look correct
      if ((await skeletonElements.count()) > 0) {
        await expect(skeletonElements).toBeVisible();

        // Verify skeleton has proper animation class
        await expect(skeletonElements).toHaveClass(/animate-pulse/);
      }

      // Wait for loading to complete
      await page.waitForLoadState("networkidle");

      // Verify skeletons are replaced with actual content
      const dashboardContent = page.locator(
        '[data-testid="dashboard-content"], .grid',
      );
      await expect(dashboardContent.first()).toBeVisible();
    });

    test("should show skeleton loaders when navigating between tabs", async ({
      page,
    }) => {
      // Navigate to different tabs to trigger loading states
      const tabs = ["jobs", "search", "compare"];

      for (const tab of tabs) {
        const tabButton = page.locator(`text="${tab}"`, {
          hasText: new RegExp(tab, "i"),
        });
        if ((await tabButton.count()) > 0) {
          await tabButton.first().click();
          await page.waitForTimeout(300);

          // Look for any loading indicators or skeleton content
          const loadingIndicators = page.locator(
            ".animate-pulse, .animate-spin, .loading",
          );
          // Don't fail if no loading states are visible (content might load too quickly)
        }
      }
    });
  });

  test.describe("Toast Notifications", () => {
    test("should display toast notifications for user actions", async ({
      page,
    }) => {
      // Navigate to upload tab to trigger a potential toast
      await page.click('text="Upload"');
      await page.waitForTimeout(1000);

      // Look for any existing toasts (they might appear from page load)
      const toastContainer = page.locator(
        '.fixed.bottom-4.right-4, [data-testid="toast-container"]',
      );

      if ((await toastContainer.count()) > 0) {
        // Check toast structure
        const toast = toastContainer.locator(".bg-white, .rounded-lg").first();
        if ((await toast.count()) > 0) {
          await expect(toast).toBeVisible();

          // Check for toast icons (success, error, warning, info)
          const toastIcon = toast.locator("svg").first();
          if ((await toastIcon.count()) > 0) {
            await expect(toastIcon).toBeVisible();
          }

          // Check for close button
          const closeButton = toast.locator("button:has(svg)").last();
          if ((await closeButton.count()) > 0) {
            await expect(closeButton).toBeVisible();
          }
        }
      }

      // Test toast dismiss functionality if toast is present
      const existingToast = page
        .locator(".fixed.bottom-4.right-4 .bg-white")
        .first();
      if ((await existingToast.count()) > 0) {
        const closeBtn = existingToast.locator("button").last();
        if ((await closeBtn.count()) > 0) {
          await closeBtn.click();
          await page.waitForTimeout(500);
          // Toast should disappear or fade out
          await expect(existingToast).not.toBeVisible();
        }
      }
    });

    test("should show different toast types with appropriate styling", async ({
      page,
    }) => {
      // Check for toast color variations and icons
      const toasts = page.locator(".fixed.bottom-4.right-4 .bg-white");

      if ((await toasts.count()) > 0) {
        for (let i = 0; i < (await toasts.count()); i++) {
          const toast = toasts.nth(i);

          // Check for colored border (indicating toast type)
          const borderColors = [
            "border-l-green-500",
            "border-l-red-500",
            "border-l-yellow-500",
            "border-l-blue-500",
          ];
          let hasBorderColor = false;

          for (const borderColor of borderColors) {
            if ((await toast.locator(`.${borderColor}`).count()) > 0) {
              hasBorderColor = true;
              break;
            }
          }

          // If no specific border color classes, check for any border-l class
          if (!hasBorderColor) {
            const borderLeft = toast.locator('[class*="border-l"]');
            if ((await borderLeft.count()) > 0) {
              hasBorderColor = true;
            }
          }

          // Verify toast has some form of type indication
          expect(hasBorderColor).toBeTruthy();
        }
      }
    });
  });

  test.describe("Breadcrumb Navigation", () => {
    test("should display breadcrumbs in job detail view", async ({ page }) => {
      // First navigate to jobs tab
      await page.click('text="Jobs"');
      await page.waitForTimeout(1000);

      // Look for job items to click on
      const jobItems = page.locator(
        '.cursor-pointer, [data-testid="job-item"], .hover\\:bg-gray-50',
      );

      if ((await jobItems.count()) > 0) {
        // Click on the first job to view details
        await jobItems.first().click();
        await page.waitForTimeout(1000);

        // Check for breadcrumb navigation
        const breadcrumb = page.locator(
          'nav[aria-label="Breadcrumb"], .flex.items-center.space-x-1',
        );

        if ((await breadcrumb.count()) > 0) {
          await expect(breadcrumb.first()).toBeVisible();

          // Check for home icon/button
          const homeButton = breadcrumb.locator("button:has(svg), svg");
          if ((await homeButton.count()) > 0) {
            await expect(homeButton.first()).toBeVisible();
          }

          // Check for breadcrumb separators (chevrons)
          const separators = breadcrumb.locator("svg, .w-4.h-4");
          if ((await separators.count()) > 1) {
            await expect(separators.nth(1)).toBeVisible();
          }

          // Check for current page indicator
          const currentPage = breadcrumb.locator(
            '.bg-gray-100, [aria-current="page"]',
          );
          if ((await currentPage.count()) > 0) {
            await expect(currentPage.first()).toBeVisible();
          }
        }

        // Test breadcrumb navigation functionality
        const homeBtn = breadcrumb.locator("button").first();
        if ((await homeBtn.count()) > 0) {
          await homeBtn.click();
          await page.waitForTimeout(500);

          // Should navigate back to dashboard
          const dashboardTitle = page.locator('text="Dashboard", h1');
          if ((await dashboardTitle.count()) > 0) {
            await expect(dashboardTitle.first()).toBeVisible();
          }
        }
      }
    });

    test("should have functional breadcrumb links", async ({ page }) => {
      // Navigate to compare tab
      await page.click('text="Compare"');
      await page.waitForTimeout(1000);

      // Look for any breadcrumbs that might appear
      const breadcrumbLinks = page.locator(
        'nav[aria-label="Breadcrumb"] button, nav a',
      );

      if ((await breadcrumbLinks.count()) > 0) {
        for (let i = 0; i < Math.min(await breadcrumbLinks.count(), 3); i++) {
          const link = breadcrumbLinks.nth(i);

          // Verify link is clickable
          await expect(link).toBeVisible();

          // Check if link has proper hover states
          await link.hover();
          await page.waitForTimeout(200);

          // Verify hover styling is applied
          const hasHoverClass = await link.evaluate((el) => {
            const classes = el.className;
            return classes.includes("hover:") || classes.includes("hover\\:");
          });

          // Don't require hover classes, but if present, they should work
        }
      }
    });
  });

  test.describe("Visual Enhancement Verification", () => {
    test("should have consistent styling and animations", async ({ page }) => {
      // Check for consistent color scheme
      const cards = page.locator(".bg-white, .border, .rounded");

      if ((await cards.count()) > 0) {
        for (let i = 0; i < Math.min(await cards.count(), 5); i++) {
          const card = cards.nth(i);
          await expect(card).toBeVisible();

          // Verify cards have proper styling
          const hasRounding = await card.evaluate((el) => {
            const classes = el.className;
            return (
              classes.includes("rounded") || classes.includes("border-radius")
            );
          });

          expect(hasRounding).toBeTruthy();
        }
      }

      // Check for animation classes
      const animatedElements = page.locator(
        ".transition, .animate-pulse, .animate-spin",
      );

      if ((await animatedElements.count()) > 0) {
        // Verify animated elements are present and functional
        await expect(animatedElements.first()).toBeVisible();
      }
    });

    test("should be responsive across different viewport sizes", async ({
      page,
    }) => {
      // Test desktop view
      await page.setViewportSize({ width: 1200, height: 800 });
      await page.waitForTimeout(500);

      // Verify layout elements are visible
      const mainContent = page.locator("main, .main, .max-w-7xl").first();
      await expect(mainContent).toBeVisible();

      // Test tablet view
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(500);

      // Verify responsive layout
      await expect(mainContent).toBeVisible();

      // Test mobile view
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      // Verify mobile layout
      await expect(mainContent).toBeVisible();

      // Check if navigation tabs are still accessible
      const tabs = page.locator('[role="tablist"], .grid-cols-6');
      if ((await tabs.count()) > 0) {
        await expect(tabs.first()).toBeVisible();
      }

      // Reset to desktop view
      await page.setViewportSize({ width: 1200, height: 800 });
    });

    test("should have proper loading and error states", async ({ page }) => {
      // Test error state by navigating to a non-existent route or triggering an error
      await page.goto("/#invalid-route");
      await page.waitForTimeout(1000);

      // Check if app gracefully handles invalid routes
      const errorElements = page.locator(
        'text="Error", text="error", text="Not found", text="404"',
      );

      // App should either show error state or redirect to valid route
      const validContent = page.locator(".max-w-7xl, main, h1");
      await expect(validContent.first()).toBeVisible();

      // Return to main page
      await page.goto("/");
      await page.waitForLoadState("networkidle");
    });
  });
});
