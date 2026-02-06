/**
 * Common test fixtures and utilities for E2E tests
 */
import { test as base, expect, Page } from '@playwright/test';

/**
 * Console error collector - fails test if uncaught JS errors occur
 */
export interface ConsoleErrorCollector {
  errors: string[];
  startCollecting: () => void;
  assertNoErrors: () => void;
}

/**
 * Extended test fixture with console error tracking
 */
export const test = base.extend<{ consoleErrors: ConsoleErrorCollector }>({
  consoleErrors: async ({ page }, use) => {
    const errors: string[] = [];
    
    const collector: ConsoleErrorCollector = {
      errors,
      startCollecting: () => {
        page.on('console', (msg) => {
          if (msg.type() === 'error') {
            // Ignore some common non-critical errors
            const text = msg.text();
            if (
              !text.includes('favicon') &&
              !text.includes('Source map') &&
              !text.includes('[HMR]') &&
              !text.includes('404') &&
              !text.includes('Failed to load resource') &&
              !text.includes('not found') && // Ignore "Exercise with ID X not found" errors
              !text.includes('replace_exercise') && // Ignore replace exercise API errors in tests
              !text.includes('swapping exercise') && // Ignore swap exercise errors
              !text.includes('UNKNOWN_ERROR') // Ignore unknown error responses from API tests
            ) {
              errors.push(text);
            }
          }
        });
        
        page.on('pageerror', (error) => {
          errors.push(`Page Error: ${error.message}`);
        });
      },
      assertNoErrors: () => {
        if (errors.length > 0) {
          throw new Error(`Console errors detected:\n${errors.join('\n')}`);
        }
      },
    };
    
    await use(collector);
  },
});

export { expect };

/**
 * Route definitions for easy reference
 */
export const ROUTES = {
  HOME: '/',
  WORKOUT_PLAN: '/workout_plan',
  WORKOUT_LOG: '/workout_log',
  WEEKLY_SUMMARY: '/weekly_summary',
  SESSION_SUMMARY: '/session_summary',
  PROGRESSION: '/progression',
  VOLUME_SPLITTER: '/volume_splitter',
} as const;

/**
 * Test selectors (data-testid) for stable element selection
 * Uses ID fallbacks for elements where data-testid might not be present
 */
export const SELECTORS = {
  // Navbar
  NAVBAR: '[data-testid="navbar"], #navbar',
  NAV_BRAND: '[data-testid="nav-brand"], #nav-brand',
  NAV_WORKOUT_PLAN: '[data-testid="nav-workout-plan"], #nav-workout-plan',
  NAV_WEEKLY_SUMMARY: '[data-testid="nav-weekly-summary"], #nav-weekly-summary',
  NAV_SESSION_SUMMARY: '[data-testid="nav-session-summary"], #nav-session-summary',
  NAV_WORKOUT_LOG: '[data-testid="nav-workout-log"], #nav-workout-log',
  NAV_PROGRESSION_PLAN: '[data-testid="nav-progression-plan"], #nav-progression-plan',
  NAV_VOLUME_SPLITTER: '[data-testid="nav-volume-splitter"], #nav-volume-splitter',
  DARK_MODE_TOGGLE: '[data-testid="dark-mode-toggle"], #darkModeToggle',
  
  // Toast notification
  TOAST_CONTAINER: '[data-testid="toast-container"], .toast-container',
  TOAST: '#liveToast',
  TOAST_BODY: '#toast-body',
  
  // Page identifiers
  PAGE_WELCOME: '[data-page="welcome"]',
  PAGE_WORKOUT_PLAN: '[data-page="workout-plan"]',
  PAGE_WORKOUT_LOG: '.workout-log-frame',
  PAGE_WEEKLY_SUMMARY: '#weekly-summary-container',
  PAGE_SESSION_SUMMARY: '#session-summary-container',
  PAGE_PROGRESSION: '.progression-plan-container',
  PAGE_VOLUME_SPLITTER: '#volume-splitter-app',
  
  // Workout Plan page elements (use ID as fallback)
  ROUTINE_ENV: '[data-testid="routine-env"], #routine-env',
  ROUTINE_PROGRAM: '[data-testid="routine-program"], #routine-program',
  ROUTINE_DAY: '[data-testid="routine-day"], #routine-day',
  FILTER_FORM: '#filters-form',
  ADD_EXERCISE_BTN: '[data-testid="add-exercise-btn"], #add_exercise_btn',
  EXERCISE_SEARCH: '[data-testid="exercise-search"], #exercise',
  EXERCISE_TABLE: '[data-testid="exercise-table"], .workout-plan-table',
  EXPORT_EXCEL_BTN: '[data-testid="export-excel-btn"], .btn-export-excel',
  EXPORT_TO_LOG_BTN: '[data-testid="export-to-log-btn"], #export-to-log-btn',
  CLEAR_FILTERS_BTN: '[data-testid="clear-filters-btn"], #clear-filters-btn',
  
  // Volume Splitter
  TRAINING_DAYS: '#training-days',
  CALCULATE_VOLUME_BTN: '#calculate-volume',
  RESET_VOLUME_BTN: '#reset-volume',
  EXPORT_VOLUME_EXCEL_BTN: '#export-to-excel-btn',
  
  // Progression page
  EXERCISE_SELECT: '#exerciseSelect',
  
  // Workout Log
  IMPORT_FROM_PLAN_BTN: '#import-from-plan-btn',
  CLEAR_LOG_BTN: '#clear-log-btn',
} as const;

/**
 * Wait for page to be fully loaded and interactive
 */
export async function waitForPageReady(page: Page): Promise<void> {
  await page.waitForLoadState('domcontentloaded');
  await page.waitForLoadState('networkidle');
}

/**
 * Assert toast notification appears with expected message
 */
export async function expectToast(page: Page, expectedText: string | RegExp): Promise<void> {
  const toast = page.locator(SELECTORS.TOAST);
  await expect(toast).toBeVisible({ timeout: 5000 });
  const toastBody = page.locator(SELECTORS.TOAST_BODY);
  await expect(toastBody).toContainText(expectedText);
}

/**
 * Get dark mode state from html element
 */
export async function getDarkModeState(page: Page): Promise<string | null> {
  return page.locator('html').getAttribute('data-theme');
}

/**
 * Check localStorage for dark mode preference
 */
export async function getStoredDarkMode(page: Page): Promise<string | null> {
  return page.evaluate(() => localStorage.getItem('darkMode'));
}
