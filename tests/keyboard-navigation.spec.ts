/**
 * Keyboard Navigation E2E Tests
 * Tests the keyboard shortcuts implementation for accessibility and usability
 */

import { test, expect } from '@playwright/test';

test.describe('Keyboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:3002');

    // Wait for the app to load
    await page.waitForSelector('[data-testid="jddb-layout"]', { timeout: 10000 });
  });

  test('should navigate between tabs using Ctrl+Number shortcuts', async ({ page }) => {
    // Test Ctrl+1 (Dashboard)
    await page.keyboard.press('Control+1');
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Dashboard', { timeout: 2000 });

    // Test Ctrl+2 (Jobs)
    await page.keyboard.press('Control+2');
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Jobs', { timeout: 2000 });

    // Test Ctrl+3 (Upload)
    await page.keyboard.press('Control+3');
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Upload', { timeout: 2000 });

    // Test Ctrl+4 (Search)
    await page.keyboard.press('Control+4');
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Search', { timeout: 2000 });

    // Test Ctrl+5 (Compare)
    await page.keyboard.press('Control+5');
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Compare', { timeout: 2000 });

    // Test Ctrl+6 (Statistics)
    await page.keyboard.press('Control+6');
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Statistics', { timeout: 2000 });
  });

  test('should focus search input with / or Ctrl+K shortcuts', async ({ page }) => {
    // Test / shortcut
    await page.keyboard.press('/');

    // Should switch to search tab
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Search', { timeout: 2000 });

    // Should focus search input after delay
    await page.waitForTimeout(200);
    const focusedElement = await page.locator(':focus');
    await expect(focusedElement).toHaveAttribute('type', 'search');

    // Test Ctrl+K shortcut from another tab
    await page.keyboard.press('Control+1'); // Go to dashboard first
    await page.keyboard.press('Control+k');

    // Should switch to search tab and focus input
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Search', { timeout: 2000 });
    await page.waitForTimeout(200);
    const focusedElement2 = await page.locator(':focus');
    await expect(focusedElement2).toHaveAttribute('type', 'search');
  });

  test('should open keyboard shortcuts modal with ? or Ctrl+H', async ({ page }) => {
    // Test ? shortcut
    await page.keyboard.press('Shift+/'); // This produces '?'

    // Modal should open
    await expect(page.locator('[data-testid="keyboard-shortcuts-modal"]')).toBeVisible({ timeout: 2000 });

    // Check modal content
    await expect(page.locator('text=Keyboard Shortcuts')).toBeVisible();
    await expect(page.locator('text=Navigation')).toBeVisible();
    await expect(page.locator('text=Search')).toBeVisible();
    await expect(page.locator('text=Actions')).toBeVisible();

    // Close modal with Escape
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-testid="keyboard-shortcuts-modal"]')).not.toBeVisible();

    // Test Ctrl+H shortcut
    await page.keyboard.press('Control+h');
    await expect(page.locator('[data-testid="keyboard-shortcuts-modal"]')).toBeVisible({ timeout: 2000 });
  });

  test('should display correct shortcut formatting', async ({ page }) => {
    // Open shortcuts modal
    await page.keyboard.press('Shift+/');

    // Check for platform-appropriate formatting
    const userAgent = await page.evaluate(() => navigator.userAgent);
    const isMac = userAgent.includes('Mac');

    if (isMac) {
      await expect(page.locator('text=⌘1')).toBeVisible();
      await expect(page.locator('text=⌘K')).toBeVisible();
    } else {
      await expect(page.locator('text=Ctrl+1')).toBeVisible();
      await expect(page.locator('text=Ctrl+K')).toBeVisible();
    }

    // Check for consistent formatting
    await expect(page.locator('text=/')).toBeVisible();
    await expect(page.locator('text=?')).toBeVisible();
  });

  test('should not interfere with input fields', async ({ page }) => {
    // Navigate to search tab
    await page.keyboard.press('Control+4');
    await page.waitForSelector('input[type="search"]', { timeout: 2000 });

    // Focus search input
    await page.click('input[type="search"]');

    // Type text that includes shortcut keys - should not trigger shortcuts
    await page.fill('input[type="search"]', 'test search /help ?query');

    // Verify text was typed normally
    const inputValue = await page.inputValue('input[type="search"]');
    expect(inputValue).toBe('test search /help ?query');

    // Should still be on search tab
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Search');
  });

  test('should show shortcut categories correctly', async ({ page }) => {
    await page.keyboard.press('Shift+/');

    // Check all categories are present
    await expect(page.locator('text=Navigation')).toBeVisible();
    await expect(page.locator('text=Search')).toBeVisible();
    await expect(page.locator('text=Actions')).toBeVisible();

    // Check specific shortcuts in each category
    await expect(page.locator('text=Navigate to Dashboard')).toBeVisible();
    await expect(page.locator('text=Focus search input')).toBeVisible();
    await expect(page.locator('text=New upload')).toBeVisible();

    // Check tips section
    await expect(page.locator('text=Tips')).toBeVisible();
    await expect(page.locator('text=Shortcuts work from anywhere except when typing')).toBeVisible();
  });

  test('should navigate to upload tab with Ctrl+N', async ({ page }) => {
    // Start from dashboard
    await page.keyboard.press('Control+1');

    // Use Ctrl+N for new upload
    await page.keyboard.press('Control+n');

    // Should switch to upload tab
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Upload', { timeout: 2000 });
  });

  test('should handle keyboard shortcuts accessibility', async ({ page }) => {
    // Test that shortcuts work without mouse interaction
    await page.keyboard.press('Control+4'); // Search
    await page.keyboard.press('/'); // Focus search
    await page.keyboard.press('Control+5'); // Compare
    await page.keyboard.press('Shift+/'); // Help modal

    // Modal should be accessible via keyboard
    await expect(page.locator('[data-testid="keyboard-shortcuts-modal"]')).toBeVisible();

    // Should be able to close with Escape
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-testid="keyboard-shortcuts-modal"]')).not.toBeVisible();

    // Should still be on compare tab
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Compare');
  });

  test('should work with different modifier key combinations', async ({ page }) => {
    // Test that Ctrl and Meta keys both work (for cross-platform compatibility)
    const isMac = await page.evaluate(() => navigator.platform.toUpperCase().indexOf('MAC') >= 0);

    if (isMac) {
      // On Mac, test Meta key (Cmd)
      await page.keyboard.press('Meta+1');
      await expect(page.locator('[data-testid="active-tab"]')).toContainText('Dashboard', { timeout: 2000 });

      await page.keyboard.press('Meta+k');
      await expect(page.locator('[data-testid="active-tab"]')).toContainText('Search', { timeout: 2000 });
    } else {
      // On PC, test Ctrl key
      await page.keyboard.press('Control+1');
      await expect(page.locator('[data-testid="active-tab"]')).toContainText('Dashboard', { timeout: 2000 });

      await page.keyboard.press('Control+k');
      await expect(page.locator('[data-testid="active-tab"]')).toContainText('Search', { timeout: 2000 });
    }
  });
});

test.describe('Keyboard Navigation Performance', () => {
  test('should respond to shortcuts quickly', async ({ page }) => {
    await page.goto('http://localhost:3002');
    await page.waitForSelector('[data-testid="jddb-layout"]');

    const startTime = Date.now();

    // Test rapid navigation
    await page.keyboard.press('Control+1');
    await page.keyboard.press('Control+2');
    await page.keyboard.press('Control+3');
    await page.keyboard.press('Control+4');

    const endTime = Date.now();
    const responseTime = endTime - startTime;

    // Should respond within reasonable time (less than 1 second for all shortcuts)
    expect(responseTime).toBeLessThan(1000);

    // Should end on search tab
    await expect(page.locator('[data-testid="active-tab"]')).toContainText('Search', { timeout: 2000 });
  });
});