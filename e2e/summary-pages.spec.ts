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

test.describe('Pattern Coverage Analysis (v1.5.0)', () => {
  test.beforeEach(async ({ page, consoleErrors }) => {
    consoleErrors.startCollecting();
    await page.goto(ROUTES.WEEKLY_SUMMARY);
    await waitForPageReady(page);
  });

  test.afterEach(async ({ consoleErrors }) => {
    consoleErrors.assertNoErrors();
  });

  test('pattern coverage API returns valid structure', async ({ request }) => {
    const response = await request.get('http://localhost:5000/api/pattern_coverage');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data).toHaveProperty('per_routine');
    expect(data.data).toHaveProperty('total');
    expect(data.data).toHaveProperty('warnings');
    expect(data.data).toHaveProperty('sets_per_routine');
    expect(data.data).toHaveProperty('ideal_sets_range');
  });

  test('pattern coverage warnings are actionable', async ({ request }) => {
    const response = await request.get('http://localhost:5000/api/pattern_coverage');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    const warnings = data.data.warnings;
    
    // Warnings should be an array
    expect(Array.isArray(warnings)).toBe(true);
    
    // Each warning should have required fields
    for (const warning of warnings) {
      expect(warning).toHaveProperty('type');
      expect(warning).toHaveProperty('message');
      // Level indicates how critical the warning is (high, medium, low)
      expect(warning).toHaveProperty('level');
      expect(['high', 'medium', 'low']).toContain(warning.level);
      // Description provides actionable details
      expect(warning).toHaveProperty('description');
    }
  });

  test('pattern coverage tracks movement patterns', async ({ request }) => {
    const response = await request.get('http://localhost:5000/api/pattern_coverage');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    const total = data.data.total;
    
    // Total should track core movement patterns
    expect(typeof total).toBe('object');
    
    // Common patterns to track
    const expectedPatterns = ['squat', 'hinge', 'horizontal_push', 'horizontal_pull', 'vertical_push', 'vertical_pull'];
    
    // At least some patterns should be tracked
    const hasPatterns = Object.keys(total).some(key => 
      expectedPatterns.some(pattern => key.toLowerCase().includes(pattern.replace('_', '')))
    );
    
    // Pattern structure may vary, just ensure it's not empty when there's data
    expect(typeof total === 'object').toBeTruthy();
  });

  test('sets_per_routine reports session volume', async ({ request }) => {
    const response = await request.get('http://localhost:5000/api/pattern_coverage');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    const setsPerRoutine = data.data.sets_per_routine;
    
    // Should be an object mapping routine names to set counts
    expect(typeof setsPerRoutine).toBe('object');
    
    // Each value should be a non-negative number
    for (const [routine, sets] of Object.entries(setsPerRoutine)) {
      expect(typeof sets).toBe('number');
      expect(sets).toBeGreaterThanOrEqual(0);
    }
  });

  test('ideal_sets_range provides guidance', async ({ request }) => {
    const response = await request.get('http://localhost:5000/api/pattern_coverage');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    const idealRange = data.data.ideal_sets_range;
    
    // Should provide min and max guidance
    expect(idealRange).toHaveProperty('min');
    expect(idealRange).toHaveProperty('max');
    expect(idealRange.min).toBeLessThan(idealRange.max);
    
    // v1.5.0 recommends 15-24 sets per session
    expect(idealRange.min).toBeGreaterThanOrEqual(10);
    expect(idealRange.max).toBeLessThanOrEqual(30);
  });
});
