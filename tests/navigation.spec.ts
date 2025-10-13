
import { test, expect } from '@playwright/test';

test.describe('App Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the initial page load - check for tab navigation instead of h1
    await page.waitForSelector('[role="tab"], button:has-text("Dashboard")');
  });

  test('should navigate to the Dashboard page', async ({ page }) => {
    await page.click('button:has-text("Dashboard")');
    await expect(page.getByRole('tab', { selected: true })).toContainText('Dashboard');
  });

  test('should navigate to the Jobs page', async ({ page }) => {
    await page.click('button:has-text("Jobs")');
    await expect(page.getByRole('tab', { selected: true })).toContainText('Jobs');
  });

  test('should navigate to the Upload page', async ({ page }) => {
    await page.click('button:has-text("Upload")');
    await expect(page.getByRole('tab', { selected: true })).toContainText('Upload');
  });

  test('should navigate to the Search page', async ({ page }) => {
    await page.click('button:has-text("Search")');
    await expect(page.getByRole('tab', { selected: true })).toContainText('Search');
  });

  test('should navigate to the Compare page', async ({ page }) => {
    await page.click('button:has-text("Compare")');
    await expect(page.getByRole('tab', { selected: true })).toContainText('Compare');
  });

  test('should navigate to the AI Demo page', async ({ page }) => {
    await page.click('button:has-text("AI Demo")');
    await expect(page.getByRole('tab', { selected: true })).toContainText('AI Demo');
  });

  test('should navigate to the Statistics page', async ({ page }) => {
    await page.click('button:has-text("Statistics")');
    await expect(page.getByRole('tab', { selected: true })).toContainText('Statistics');
  });
});
