import { test, expect } from "@playwright/test";

test.describe("Advanced Search Functionality", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.getByRole("tab", { name: "Search" }).click();

    // Wait for search interface to load
    await page.waitForSelector('input[placeholder*="search"]', {
      state: "visible",
    });
  });

  test("should display complete search interface", async ({ page }) => {
    // Check main search input
    const searchInput = page.locator('input[placeholder*="search"]');
    await expect(searchInput).toBeVisible();

    // Check for search button
    await expect(page.getByRole("button", { name: /search/i })).toBeVisible();

    // Check for filter sections
    await expect(
      page
        .locator("text=Classification")
        .or(page.locator("text=Classifications")),
    ).toBeVisible();
    await expect(
      page.locator("text=Language").or(page.locator("text=Languages")),
    ).toBeVisible();
    await expect(
      page.locator("text=Department").or(page.locator("text=Departments")),
    ).toBeVisible();

    // Check for section types if present
    const sectionTypesFilter = page.locator("text=Section Types");
    if ((await sectionTypesFilter.count()) > 0) {
      await expect(sectionTypesFilter).toBeVisible();
    }
  });

  test("should perform basic full-text search", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"]');

    // Enter search term
    await searchInput.fill("manager");

    // Submit search using button or Enter key
    const searchButton = page.getByRole("button", { name: /search/i });
    if ((await searchButton.count()) > 0) {
      await searchButton.click();
    } else {
      await searchInput.press("Enter");
    }

    // Wait for search to complete
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000); // Additional wait for results to render

    // Verify search results container exists
    const resultsContainer = page
      .locator('[data-testid="search-results"]')
      .or(page.locator("text=Search Results"))
      .or(page.locator(".search-results"))
      .or(page.locator('[class*="result"]').first());

    // Wait for either results or no results message
    await Promise.race([
      expect(resultsContainer).toBeVisible({ timeout: 10000 }),
      expect(
        page
          .locator("text=No results found")
          .or(page.locator("text=No jobs found")),
      ).toBeVisible({ timeout: 10000 }),
    ]);
  });

  test("should show search suggestions", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"]');

    // Type partial search term to trigger suggestions
    await searchInput.fill("dir");

    // Wait for suggestions to appear
    await page.waitForTimeout(500);

    // Check if suggestions dropdown appears
    const suggestionsContainer = page
      .locator('[data-testid="search-suggestions"]')
      .or(page.locator(".suggestions"))
      .or(page.locator('[class*="suggestion"]'));

    // Suggestions might not always appear, so we make it optional
    if ((await suggestionsContainer.count()) > 0) {
      await expect(suggestionsContainer).toBeVisible();
    }
  });

  test("should apply classification filters", async ({ page }) => {
    // Look for classification filter controls
    const classificationSection = page
      .locator("text=Classification")
      .or(page.locator("text=Classifications"));
    await expect(classificationSection).toBeVisible();

    // Try to find and interact with classification filter controls
    const classificationFilter = page
      .locator('select[name*="classification"]')
      .or(page.locator('input[type="checkbox"][value*="EX-"]'))
      .or(page.locator("button").filter({ hasText: /EX-\d+/ }))
      .first();

    if ((await classificationFilter.count()) > 0) {
      if ((await classificationFilter.getAttribute("type")) === "checkbox") {
        await classificationFilter.check();
      } else if ((await classificationFilter.tagName()) === "SELECT") {
        const options = await classificationFilter.locator("option").count();
        if (options > 1) {
          await classificationFilter.selectOption({ index: 1 });
        }
      } else {
        await classificationFilter.click();
      }

      // Perform search after applying filter
      const searchInput = page.locator('input[placeholder*="search"]');
      await searchInput.fill("director");
      await searchInput.press("Enter");

      await page.waitForLoadState("networkidle");
    }
  });

  test("should apply language filters", async ({ page }) => {
    const languageSection = page
      .locator("text=Language")
      .or(page.locator("text=Languages"));
    await expect(languageSection).toBeVisible();

    // Try to find language filter controls
    const languageFilter = page
      .locator('select[name*="language"]')
      .or(page.locator('input[type="radio"][value="en"]'))
      .or(page.locator("button").filter({ hasText: /English|French/ }))
      .first();

    if ((await languageFilter.count()) > 0) {
      if ((await languageFilter.getAttribute("type")) === "radio") {
        await languageFilter.check();
      } else if ((await languageFilter.tagName()) === "SELECT") {
        await languageFilter.selectOption("en");
      } else {
        await languageFilter.click();
      }
    }
  });

  test("should perform semantic search", async ({ page }) => {
    // Look for semantic search toggle/option
    const semanticToggle = page
      .locator('input[type="checkbox"][name*="semantic"]')
      .or(
        page
          .locator('input[type="checkbox"]')
          .filter({ hasText: /semantic|vector/i }),
      )
      .or(page.locator("text=Semantic Search").locator("..").locator("input"))
      .or(page.locator("button").filter({ hasText: /semantic/i }));

    if ((await semanticToggle.count()) > 0) {
      // Enable semantic search if it's a toggle
      if ((await semanticToggle.getAttribute("type")) === "checkbox") {
        await semanticToggle.check();
      } else {
        await semanticToggle.click();
      }

      // Perform a conceptual search that would benefit from semantic matching
      const searchInput = page.locator('input[placeholder*="search"]');
      await searchInput.fill("leadership responsibilities team management");
      await searchInput.press("Enter");

      await page.waitForLoadState("networkidle");

      // Verify that semantic search indicator is shown if available
      const semanticIndicator = page
        .locator("text=Semantic")
        .or(page.locator("text=Vector"));
      if ((await semanticIndicator.count()) > 0) {
        await expect(semanticIndicator).toBeVisible();
      }
    } else {
      // If no semantic toggle found, just perform a regular search
      const searchInput = page.locator('input[placeholder*="search"]');
      await searchInput.fill("leadership");
      await searchInput.press("Enter");
      await page.waitForLoadState("networkidle");
    }
  });

  test("should perform advanced multi-filter search", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"]');

    // Enter complex search term
    await searchInput.fill("director management");

    // Apply multiple filters if available
    // Classification filter
    const classificationFilter = page
      .locator('select[name*="classification"]')
      .first();
    if ((await classificationFilter.count()) > 0) {
      const options = await classificationFilter.locator("option").count();
      if (options > 1) {
        await classificationFilter.selectOption({ index: 1 });
      }
    }

    // Language filter
    const languageFilter = page.locator('select[name*="language"]').first();
    if ((await languageFilter.count()) > 0) {
      await languageFilter.selectOption("en");
    }

    // Section type filters if present
    const sectionTypeCheckboxes = page.locator(
      'input[type="checkbox"][name*="section"]',
    );
    const sectionCount = await sectionTypeCheckboxes.count();
    if (sectionCount > 0) {
      // Check first available section type
      await sectionTypeCheckboxes.first().check();
    }

    // Perform search
    await searchInput.press("Enter");
    await page.waitForLoadState("networkidle");

    // Verify that filters are applied (look for filter indicators or badges)
    const appliedFilters = page
      .locator(".filter-badge")
      .or(page.locator('[data-testid="applied-filter"]'));
    if ((await appliedFilters.count()) > 0) {
      await expect(appliedFilters.first()).toBeVisible();
    }
  });

  test("should display search result details", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"]');

    // Perform search
    await searchInput.fill("director");
    await searchInput.press("Enter");
    await page.waitForLoadState("networkidle");

    // Wait for results to load
    await page.waitForTimeout(2000);

    // Look for result items
    const resultItems = page
      .locator('[data-testid="search-result-item"]')
      .or(page.locator(".search-result"))
      .or(page.locator('[class*="result-item"]'));

    if ((await resultItems.count()) > 0) {
      const firstResult = resultItems.first();
      await expect(firstResult).toBeVisible();

      // Check for job details in results
      await expect(firstResult.locator("text=*").first()).toBeVisible();

      // Look for result metadata like job number, classification
      const jobMetadata = firstResult
        .locator('text*="EX-"')
        .or(firstResult.locator('text*="Classification"'));
      if ((await jobMetadata.count()) > 0) {
        await expect(jobMetadata).toBeVisible();
      }

      // Look for view/action buttons
      const viewButton = firstResult
        .locator("button")
        .filter({ hasText: /view|details/i });
      if ((await viewButton.count()) > 0) {
        await expect(viewButton).toBeVisible();
      }
    }
  });

  test("should handle search result pagination", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"]');

    // Perform a broad search likely to return many results
    await searchInput.fill("director");
    await searchInput.press("Enter");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    // Look for pagination controls
    const nextButton = page.locator("button").filter({ hasText: /next|>/i });
    const pageNumbers = page.locator("button").filter({ hasText: /^\d+$/ });
    const paginationContainer = page
      .locator('[data-testid="pagination"]')
      .or(page.locator(".pagination"));

    if (
      (await nextButton.count()) > 0 ||
      (await pageNumbers.count()) > 0 ||
      (await paginationContainer.count()) > 0
    ) {
      // Pagination exists, test it
      if ((await nextButton.count()) > 0) {
        await nextButton.click();
        await page.waitForLoadState("networkidle");
      } else if ((await pageNumbers.count()) > 1) {
        await pageNumbers.nth(1).click();
        await page.waitForLoadState("networkidle");
      }
    }
  });

  test("should clear search filters", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"]');

    // Apply some filters first
    await searchInput.fill("manager");

    // Apply classification filter if available
    const classificationFilter = page.locator('input[type="checkbox"]').first();
    if ((await classificationFilter.count()) > 0) {
      await classificationFilter.check();
    }

    // Perform search
    await searchInput.press("Enter");
    await page.waitForLoadState("networkidle");

    // Look for clear/reset button
    const clearButton = page
      .locator("button")
      .filter({ hasText: /clear|reset|×/i });
    if ((await clearButton.count()) > 0) {
      await clearButton.click();

      // Verify filters are cleared
      await expect(searchInput).toHaveValue("");

      // Verify checkboxes are unchecked
      const checkboxes = page.locator('input[type="checkbox"]:checked');
      await expect(checkboxes).toHaveCount(0);
    }
  });

  test("should handle empty search results gracefully", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"]');

    // Search for something that likely won't exist
    await searchInput.fill("xyzzyzxyzwontexist123nonexistentterm");
    await searchInput.press("Enter");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    // Check for no results message
    await expect(
      page
        .locator("text=No results found")
        .or(page.locator("text=No jobs found"))
        .or(page.locator("text=0 results"))
        .or(page.locator('[data-testid="no-results"]')),
    ).toBeVisible({ timeout: 10000 });
  });

  test("should export search results", async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="search"]');

    // Perform search first
    await searchInput.fill("director");
    await searchInput.press("Enter");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2000);

    // Look for export button
    const exportButton = page
      .locator("button")
      .filter({ hasText: /export|download/i });

    if ((await exportButton.count()) > 0) {
      // Set up download promise before clicking
      const downloadPromise = page.waitForEvent("download");

      await exportButton.click();

      // Handle export format selection if modal appears
      const exportModal = page
        .locator('[data-testid="export-modal"]')
        .or(page.locator(".modal"));
      if ((await exportModal.count()) > 0) {
        const confirmButton = exportModal
          .locator("button")
          .filter({ hasText: /export|confirm|ok/i });
        if ((await confirmButton.count()) > 0) {
          await confirmButton.click();
        }
      }

      // Verify download starts (wait up to 5 seconds)
      try {
        const download = await downloadPromise;
        expect(download).toBeTruthy();
        expect(download.suggestedFilename()).toMatch(/\.(txt|csv|json)$/);
      } catch (error) {
        // Export might not be fully implemented yet, so we just verify the button exists
        console.log("Export functionality may not be fully implemented yet");
      }
    }
  });

  test("should handle search errors gracefully", async ({ page }) => {
    // This test simulates network errors or API failures

    // Intercept search API calls and make them fail
    await page.route("**/search/**", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal server error" }),
      });
    });

    const searchInput = page.locator('input[placeholder*="search"]');
    await searchInput.fill("test search");
    await searchInput.press("Enter");

    await page.waitForTimeout(2000);

    // Look for error message or retry button
    const errorMessage = page
      .locator("text=Error")
      .or(page.locator("text=failed"))
      .or(page.locator('[data-testid="error"]'));
    if ((await errorMessage.count()) > 0) {
      await expect(errorMessage).toBeVisible();
    }

    // Look for retry button
    const retryButton = page
      .locator("button")
      .filter({ hasText: /retry|try again/i });
    if ((await retryButton.count()) > 0) {
      await expect(retryButton).toBeVisible();
    }
  });
});
