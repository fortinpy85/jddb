
import { test, expect } from '@playwright/test';

test.describe('App Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3002/');
    // Wait for the initial page load
    await page.waitForSelector('main h1, h1:has-text("Job Descriptions")');
  });

  test('should navigate to the Dashboard page', async ({ page }) => {
    await page.click('button:has-text("Dashboard")');
    await expect(page.locator('main h1:has-text("Dashboard"), h1:has-text("Dashboard")').first()).toBeVisible();
  });

  test('should navigate to the Jobs page', async ({ page }) => {
    await page.click('button:has-text("Jobs")');
    await expect(page.locator('main h1:has-text("Job Descriptions"), h1:has-text("Job Descriptions")').first()).toBeVisible();
  });

  test('should navigate to the Upload page', async ({ page }) => {
    await page.click('button:has-text("Upload")');
    await expect(page.locator('h2:has-text("Bulk File Upload")')).toBeVisible();
  });

  test('should navigate to the Search page', async ({ page }) => {
    await page.click('button:has-text("Search")');
    await expect(page.locator('h2:has-text("Advanced Job Search")')).toBeVisible();
  });

  test('should navigate to the Compare page', async ({ page }) => {
    await page.click('button:has-text("Compare")');
    await expect(page.locator('h2:has-text("Job Comparison Tool")')).toBeVisible();
  });

  test('should navigate to the AI Demo page', async ({ page }) => {
    await page.click('button:has-text("AI Demo")');
    await expect(page.locator('main h1:has-text("AI Features Demo"), h1:has-text("AI Features Demo")').first()).toBeVisible();
  });

  test('should navigate to the Statistics page', async ({ page }) => {
    await page.click('button:has-text("Statistics")');
    await expect(page.locator('main h1:has-text("Statistics"), h1:has-text("Statistics")').first()).toBeVisible();
  });
});
