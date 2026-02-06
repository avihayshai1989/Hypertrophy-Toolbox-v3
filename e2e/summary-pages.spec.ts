/**
 * E2E Test: Summary Pages (Weekly & Session)
 * 
 * Tests the summary pages functionality including:
 * - Page loading
 * - Calculation mode toggles
 * - Volume legend display
 * - Table rendering
 */
import { test, expect, ROUTES, SELECTORS, waitForPageReady } from './fixtures';

test.describe('Weekly Summary Page', () => {
  test.beforeEach(async ({ page, consoleErrors }) => {
    consoleErrors.startCollecting();
    await page.goto(ROUTES.WEEKLY_SUMMARY);
    await waitForPageReady(page);
  });

  test.afterEach(async ({ consoleErrors }) => {
    consoleErrors.assertNoErrors();
  });

  test('page loads with correct structure', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1')).toContainText('Weekly Summary');

    // Check summary container
    await expect(page.locator(SELECTORS.PAGE_WEEKLY_SUMMARY)).toBeVisible();
  });

  test('calculation mode selectors are present', async ({ page }) => {
    // Check counting mode selector
    const countingMode = page.locator('#counting-mode');
    await expect(countingMode).toBeVisible();

    // Check it has the expected options
    const countingOptions = countingMode.locator('option');
    const countingCount = await countingOptions.count();
    expect(countingCount).toBeGreaterThanOrEqual(2);

    // Check contribution mode selector
    const contributionMode = page.locator('#contribution-mode');
    await expect(contributionMode).toBeVisible();

    // Check it has the expected options
    const contributionOptions = contributionMode.locator('option');
    const contributionCount = await contributionOptions.count();
    expect(contributionCount).toBeGreaterThanOrEqual(2);
  });

  test('volume legend is displayed', async ({ page }) => {
    const legend = page.locator('.volume-legend');
    await expect(legend).toBeVisible();

    // Check legend categories
    await expect(legend).toContainText('Low Volume');
    await expect(legend).toContainText('Medium Volume');
    await expect(legend).toContainText('High Volume');
    await expect(legend).toContainText('Excessive Volume');
  });

  test('weekly summary table has correct headers', async ({ page }) => {
    const table = page.locator('#weekly-summary-container table');
    await expect(table).toBeVisible();

    // Check expected headers
    const headers = table.locator('thead th');
    const headerTexts = await headers.allInnerTexts();
    const headerString = headerTexts.join(' ').toLowerCase();

    expect(headerString).toContain('muscle');
    expect(headerString).toContain('effective sets');
    expect(headerString).toContain('raw sets');
    expect(headerString).toContain('volume');
  });

  test('changing counting mode updates display', async ({ page }) => {
    const countingMode = page.locator('#counting-mode');
    
    // Select "Raw Sets" option
    await countingMode.selectOption('raw');

    // Wait for update (the function is called on change)
    await page.waitForTimeout(500);

    // The selection should persist
    await expect(countingMode).toHaveValue('raw');

    // Switch back to effective
    await countingMode.selectOption('effective');
    await page.waitForTimeout(500);
    await expect(countingMode).toHaveValue('effective');
  });

  test('changing contribution mode updates display', async ({ page }) => {
    const contributionMode = page.locator('#contribution-mode');
    
    // Select "Direct Only" option
    await contributionMode.selectOption('direct');

    // Wait for update
    await page.waitForTimeout(500);

    // The selection should persist
    await expect(contributionMode).toHaveValue('direct');

    // Switch back to total
    await contributionMode.selectOption('total');
    await page.waitForTimeout(500);
    await expect(contributionMode).toHaveValue('total');
  });
});

test.describe('Session Summary Page', () => {
  test.beforeEach(async ({ page, consoleErrors }) => {
    consoleErrors.startCollecting();
    await page.goto(ROUTES.SESSION_SUMMARY);
    await waitForPageReady(page);
  });

  test.afterEach(async ({ consoleErrors }) => {
    consoleErrors.assertNoErrors();
  });

  test('page loads with correct structure', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1')).toContainText('Session Summary');

    // Check summary container
    await expect(page.locator(SELECTORS.PAGE_SESSION_SUMMARY)).toBeVisible();
  });

  test('calculation mode selectors are present', async ({ page }) => {
    // Check counting mode selector
    const countingMode = page.locator('#counting-mode');
    await expect(countingMode).toBeVisible();

    // Check contribution mode selector  
    const contributionMode = page.locator('#contribution-mode');
    await expect(contributionMode).toBeVisible();
  });

  test('volume legend is displayed', async ({ page }) => {
    const legend = page.locator('.volume-legend');
    await expect(legend).toBeVisible();

    // Check session-specific content
    await expect(legend).toContainText('Volume Classification');
  });

  test('session summary table has correct headers', async ({ page }) => {
    const table = page.locator('#session-summary-container table');
    await expect(table).toBeVisible();

    // Check expected headers
    const headers = table.locator('thead th');
    const headerTexts = await headers.allInnerTexts();
    const headerString = headerTexts.join(' ').toLowerCase();

    expect(headerString).toContain('routine');
    expect(headerString).toContain('muscle');
    expect(headerString).toContain('effective sets');
    expect(headerString).toContain('volume');
  });

  test('method selector section has descriptions', async ({ page }) => {
    const methodSelector = page.locator('.method-selector');
    await expect(methodSelector).toBeVisible();

    // Check help text exists (multiple form-text elements, check at least one is visible)
    const formTexts = methodSelector.locator('.form-text');
    await expect(formTexts.first()).toBeVisible();
  });
});
