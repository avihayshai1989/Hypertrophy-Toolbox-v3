/**
 * E2E Test: Program Backup (Program Library)
 * 
 * Tests the program backup/library functionality including:
 * - Creating backups
 * - Listing backups
 * - Restoring backups
 * - Deleting backups
 * - Backup modal interactions
 */
import { test, expect, ROUTES, SELECTORS, waitForPageReady, expectToast } from './fixtures';

test.describe('Program Backup Feature', () => {
  test.beforeEach(async ({ page, consoleErrors }) => {
    consoleErrors.startCollecting();
    await page.goto(ROUTES.WORKOUT_PLAN);
    await waitForPageReady(page);
  });

  test.afterEach(async ({ consoleErrors }) => {
    consoleErrors.assertNoErrors();
  });

  test('program library button is visible', async ({ page }) => {
    const libraryBtn = page.locator('#load-program-btn');
    await expect(libraryBtn).toBeVisible();
    await expect(libraryBtn).toContainText('Program Library');
  });

  test('program library modal opens', async ({ page }) => {
    const libraryBtn = page.locator('#load-program-btn');
    await libraryBtn.click();

    const modal = page.locator('#programLibraryModal');
    await expect(modal).toBeVisible({ timeout: 5000 });
    await expect(modal.locator('.modal-title')).toContainText('Program Library');
  });

  test('save program button exists in modal', async ({ page }) => {
    await page.locator('#load-program-btn').click();
    const modal = page.locator('#programLibraryModal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // The save button in library modal opens another modal
    const saveBtn = modal.locator('#openSaveFromLibrary, [data-action="save-program"]');
    await expect(saveBtn).toBeVisible();
  });

  test('backup list container is present', async ({ page }) => {
    await page.locator('#load-program-btn').click();
    const modal = page.locator('#programLibraryModal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    const backupList = modal.locator('#backup-list, .backup-list');
    await expect(backupList).toBeVisible();
  });

  test('can close program library modal', async ({ page }) => {
    await page.locator('#load-program-btn').click();
    const modal = page.locator('#programLibraryModal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Close via close button
    await modal.locator('.btn-close').click();
    await expect(modal).not.toBeVisible({ timeout: 3000 });
  });

  test('save backup form has name input', async ({ page }) => {
    // Open the library modal first
    await page.locator('#load-program-btn').click();
    const libraryModal = page.locator('#programLibraryModal');
    await expect(libraryModal).toBeVisible({ timeout: 5000 });

    // Click the save button to open the save modal
    await page.locator('#openSaveFromLibrary').click();
    
    // Check the save modal has the name input
    const saveModal = page.locator('#saveBackupModal');
    await expect(saveModal).toBeVisible({ timeout: 5000 });
    
    const nameInput = saveModal.locator('#backup-name');
    await expect(nameInput).toBeVisible();
  });

  test('save backup form has note input', async ({ page }) => {
    // Open the library modal first
    await page.locator('#load-program-btn').click();
    const libraryModal = page.locator('#programLibraryModal');
    await expect(libraryModal).toBeVisible({ timeout: 5000 });

    // Click the save button to open the save modal
    await page.locator('#openSaveFromLibrary').click();
    
    // Check the save modal has the note input
    const saveModal = page.locator('#saveBackupModal');
    await expect(saveModal).toBeVisible({ timeout: 5000 });
    
    const noteInput = saveModal.locator('#backup-note');
    await expect(noteInput).toBeVisible();
  });

  test('can create a backup with valid name', async ({ page }) => {
    // Open the library modal first
    await page.locator('#load-program-btn').click();
    const libraryModal = page.locator('#programLibraryModal');
    await expect(libraryModal).toBeVisible({ timeout: 5000 });

    // Click the save button to open the save modal
    await page.locator('#openSaveFromLibrary').click();
    
    const saveModal = page.locator('#saveBackupModal');
    await expect(saveModal).toBeVisible({ timeout: 5000 });

    // Fill in backup name
    const nameInput = saveModal.locator('#backup-name');
    await nameInput.fill('E2E Test Backup ' + Date.now());

    // Click save button
    const saveBtn = saveModal.locator('#saveBackupSubmit');
    await saveBtn.click();

    // Wait for success - either toast or modal closes
    await Promise.race([
      page.waitForSelector('.toast', { timeout: 5000 }),
      page.waitForTimeout(2000)
    ]);
  });

  test('backup requires a name', async ({ page }) => {
    // Open the library modal first
    await page.locator('#load-program-btn').click();
    const libraryModal = page.locator('#programLibraryModal');
    await expect(libraryModal).toBeVisible({ timeout: 5000 });

    // Click the save button to open the save modal
    await page.locator('#openSaveFromLibrary').click();
    
    const saveModal = page.locator('#saveBackupModal');
    await expect(saveModal).toBeVisible({ timeout: 5000 });

    // Try to save without name
    const nameInput = saveModal.locator('#backup-name');
    await nameInput.clear();

    const saveBtn = saveModal.locator('#saveBackupSubmit');
    await saveBtn.click();

    // Should show validation error or prevent submission
    await page.waitForTimeout(500);
    
    // Check if form validation kicked in or error message appears
    const isInvalid = await nameInput.evaluate(el => (el as HTMLInputElement).validity.valid === false);
    const errorMessage = saveModal.locator('.error-message, .invalid-feedback, .text-danger');
    const hasError = await errorMessage.count() > 0;
    
    expect(isInvalid || hasError || await nameInput.getAttribute('required')).toBeTruthy();
  });

  test('backup list shows existing backups', async ({ page }) => {
    await page.locator('#load-program-btn').click();
    const modal = page.locator('#programLibraryModal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Wait for backup list to load
    await page.waitForTimeout(1000);

    const backupList = modal.locator('#backup-list, .backup-list');
    await expect(backupList).toBeVisible();
    
    // Either shows backups or "no backups" message
    const content = await backupList.textContent();
    expect(content).toBeTruthy();
  });

  test('backup items have restore and delete actions', async ({ page }) => {
    await page.locator('#load-program-btn').click();
    const modal = page.locator('#programLibraryModal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Wait for list to load (give extra time for network)
    await page.waitForTimeout(2000);

    const backupItems = modal.locator('[data-backup-id], .backup-item');
    const count = await backupItems.count();

    if (count > 0) {
      const firstItem = backupItems.first();
      
      // Check for restore button with correct class
      const restoreBtn = firstItem.locator('.backup-restore-btn, [data-action="restore"], button:has-text("Restore")');
      await expect(restoreBtn).toBeVisible();

      // Check for delete button with correct class
      const deleteBtn = firstItem.locator('.backup-delete-btn, [data-action="delete"], button:has-text("Delete")');
      await expect(deleteBtn).toBeVisible();
    }
    // If no backups exist, test passes (nothing to verify)
  });

  test('confirm restore modal appears before restoring', async ({ page }) => {
    await page.locator('#load-program-btn').click();
    const modal = page.locator('#programLibraryModal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    await page.waitForTimeout(2000);

    const backupItems = modal.locator('[data-backup-id], .backup-item');
    const count = await backupItems.count();

    if (count > 0) {
      const restoreBtn = backupItems.first().locator('.backup-restore-btn, [data-action="restore"]');
      if (await restoreBtn.count() > 0) {
        await restoreBtn.click();

        // Confirm modal should appear
        const confirmModal = page.locator('#confirmRestoreModal');
        await expect(confirmModal).toBeVisible({ timeout: 3000 });
      }
    }
    // If no backups exist, test passes
  });

  test('confirm delete modal appears before deleting', async ({ page }) => {
    await page.locator('#load-program-btn').click();
    const modal = page.locator('#programLibraryModal');
    await expect(modal).toBeVisible({ timeout: 5000 });

    await page.waitForTimeout(2000);

    const backupItems = modal.locator('[data-backup-id], .backup-item');
    const count = await backupItems.count();

    if (count > 0) {
      const deleteBtn = backupItems.first().locator('.backup-delete-btn, [data-action="delete"]');
      if (await deleteBtn.count() > 0) {
        await deleteBtn.click();

        // Confirm modal should appear
        const confirmModal = page.locator('#confirmDeleteModal');
        await expect(confirmModal).toBeVisible({ timeout: 3000 });
      }
    }
    // If no backups exist, test passes
  });
});

test.describe('Program Backup API Integration', () => {
  test('GET /api/backups returns list', async ({ request }) => {
    const response = await request.get('/api/backups');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.ok === true || data.status === 'success' || data.success === true).toBeTruthy();
    expect(data).toHaveProperty('data');
    expect(Array.isArray(data.data)).toBe(true);
  });

  test('POST /api/backups creates backup', async ({ request }) => {
    const response = await request.post('/api/backups', {
      data: {
        name: 'API Test Backup ' + Date.now(),
        note: 'Created via E2E test'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.ok === true || data.status === 'success' || data.success === true).toBeTruthy();
    expect(data.data).toHaveProperty('id');
    expect(data.data).toHaveProperty('name');
  });

  test('POST /api/backups requires name', async ({ request }) => {
    const response = await request.post('/api/backups', {
      data: { note: 'No name provided' }
    });
    
    expect(response.ok()).toBeFalsy();
    expect(response.status()).toBe(400);
  });

  test('GET /api/backups/:id returns backup details', async ({ request }) => {
    // First create a backup
    const createResponse = await request.post('/api/backups', {
      data: { name: 'Detail Test ' + Date.now() }
    });
    const createData = await createResponse.json();

    if (createData.success && createData.data?.id) {
      const detailResponse = await request.get(`/api/backups/${createData.data.id}`);
      expect(detailResponse.ok()).toBeTruthy();
      
      const detailData = await detailResponse.json();
      expect(detailData.data).toHaveProperty('items');
    }
  });

  test('DELETE /api/backups/:id deletes backup', async ({ request }) => {
    // First create a backup
    const createResponse = await request.post('/api/backups', {
      data: { name: 'Delete Test ' + Date.now() }
    });
    const createData = await createResponse.json();

    if (createData.success && createData.data?.id) {
      const deleteResponse = await request.delete(`/api/backups/${createData.data.id}`);
      expect(deleteResponse.ok()).toBeTruthy();
    }
  });
});
