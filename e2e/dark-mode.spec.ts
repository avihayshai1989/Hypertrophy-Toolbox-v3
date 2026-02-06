/**
 * E2E Test: Dark Mode Persistence
 * 
 * Tests that dark mode toggle works correctly and
 * persists across page reloads.
 */
import { test, expect, ROUTES, SELECTORS, waitForPageReady, getDarkModeState, getStoredDarkMode } from './fixtures';
import { Page } from '@playwright/test';

/**
 * Click the dark mode toggle using JavaScript evaluation.
 * Bypasses Playwright's actionability checks which fail due to navbar CSS zoom.
 */
async function clickDarkModeToggle(page: Page): Promise<void> {
  await page.evaluate(() => {
    const toggle = document.querySelector('#darkModeToggle') as HTMLElement;
    if (toggle) toggle.click();
  });
  await page.waitForTimeout(100); // Small delay for theme transition
}

test.describe('Dark Mode Persistence', () => {
  test.beforeEach(async ({ page, consoleErrors }) => {
    consoleErrors.startCollecting();
    // Clear localStorage before each test to ensure clean state
    await page.goto(ROUTES.HOME);
    await page.evaluate(() => localStorage.clear());
  });

  test.afterEach(async ({ consoleErrors }) => {
    consoleErrors.assertNoErrors();
  });

  test('dark mode toggle changes theme from light to dark', async ({ page }) => {
    await page.goto(ROUTES.HOME);
    await waitForPageReady(page);

    // Get initial state - should be light by default (or system preference)
    const initialTheme = await getDarkModeState(page);
    
    // Click dark mode toggle via JS (bypasses CSS zoom issues)
    const toggle = page.locator(SELECTORS.DARK_MODE_TOGGLE);
    await expect(toggle).toBeVisible();
    await clickDarkModeToggle(page);

    // Theme should have changed
    const newTheme = await getDarkModeState(page);
    expect(newTheme).not.toBe(initialTheme);
  });

  test('dark mode preference persists in localStorage', async ({ page }) => {
    await page.goto(ROUTES.HOME);
    await waitForPageReady(page);

    // Click dark mode toggle via JS
    await clickDarkModeToggle(page);

    // Check localStorage
    const storedValue = await getStoredDarkMode(page);
    expect(storedValue).toBe('true');

    // Click again to toggle back
    await clickDarkModeToggle(page);

    // Check localStorage updated
    const storedValue2 = await getStoredDarkMode(page);
    expect(storedValue2).toBe('false');
  });

  test('dark mode persists after page reload', async ({ page }) => {
    await page.goto(ROUTES.HOME);
    await waitForPageReady(page);

    // Click dark mode toggle to enable dark mode
    const toggle = page.locator(SELECTORS.DARK_MODE_TOGGLE);
    await clickDarkModeToggle(page);

    // Verify dark mode is active
    const themeBeforeReload = await getDarkModeState(page);
    expect(themeBeforeReload).toBe('dark');

    // Reload the page
    await page.reload();
    await waitForPageReady(page);

    // Dark mode should still be active
    const themeAfterReload = await getDarkModeState(page);
    expect(themeAfterReload).toBe('dark');

    // Toggle button text should show "Light Mode" when dark mode is active
    const toggleText = await toggle.locator('span').textContent();
    expect(toggleText).toContain('Light Mode');
  });

  test('toggle back to light mode works correctly', async ({ page }) => {
    await page.goto(ROUTES.HOME);
    await waitForPageReady(page);

    // Enable dark mode
    await clickDarkModeToggle(page);
    expect(await getDarkModeState(page)).toBe('dark');

    // Disable dark mode (go back to light)
    await clickDarkModeToggle(page);
    expect(await getDarkModeState(page)).toBe('light');

    // Reload and verify light mode persists
    await page.reload();
    await waitForPageReady(page);
    expect(await getDarkModeState(page)).toBe('light');
  });

  test('dark mode persists across different pages', async ({ page }) => {
    await page.goto(ROUTES.HOME);
    await waitForPageReady(page);

    // Enable dark mode
    await clickDarkModeToggle(page);
    expect(await getDarkModeState(page)).toBe('dark');

    // Navigate to different pages and verify dark mode persists
    await page.goto(ROUTES.WORKOUT_PLAN);
    await waitForPageReady(page);
    expect(await getDarkModeState(page)).toBe('dark');

    await page.goto(ROUTES.WEEKLY_SUMMARY);
    await waitForPageReady(page);
    expect(await getDarkModeState(page)).toBe('dark');

    await page.goto(ROUTES.VOLUME_SPLITTER);
    await waitForPageReady(page);
    expect(await getDarkModeState(page)).toBe('dark');
  });

  test('toggle icon changes correctly with theme', async ({ page }) => {
    await page.goto(ROUTES.HOME);
    await waitForPageReady(page);

    const toggle = page.locator(SELECTORS.DARK_MODE_TOGGLE);
    const icon = toggle.locator('i');

    // Initial state - light mode should show moon icon
    await expect(icon).toHaveClass(/fa-moon/);

    // Toggle to dark mode - should show sun icon
    await clickDarkModeToggle(page);
    await expect(icon).toHaveClass(/fa-sun/);

    // Toggle back to light mode - should show moon icon again
    await clickDarkModeToggle(page);
    await expect(icon).toHaveClass(/fa-moon/);
  });
});
