import { test, expect } from '@playwright/test';

/**
 * LOW ENHANCEMENT: E2E tests for consumer scan workflow
 * 
 * Tests the complete user journey:
 * 1. User visits scan page
 * 2. User enters tag ID
 * 3. System validates input
 * 4. System shows scan results
 * 5. System displays product information
 */

test.describe('Consumer Scan Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to scan page
    await page.goto('/scan');
  });

  test('should display scan page correctly', async ({ page }) => {
    // Verify page title
    await expect(page).toHaveTitle(/VokeTag/i);
    
    // Verify scan form is present
    await expect(page.locator('form')).toBeVisible();
    
    // Verify input field
    const input = page.locator('input[type="text"]');
    await expect(input).toBeVisible();
    await expect(input).toHaveAttribute('placeholder', /tag.*id/i);
    
    // Verify submit button
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toHaveText(/scan|verify/i);
  });

  test('should validate empty input', async ({ page }) => {
    // Try to submit empty form
    await page.locator('button[type="submit"]').click();
    
    // Should show validation error
    await expect(page.locator('[role="alert"]')).toContainText(/required|invalid/i);
  });

  test('should validate invalid UUID format', async ({ page }) => {
    // Enter invalid UUID
    await page.locator('input[type="text"]').fill('invalid-uuid');
    await page.locator('button[type="submit"]').click();
    
    // Should show validation error
    await expect(page.locator('[role="alert"]')).toContainText(/invalid.*uuid|invalid.*format/i);
  });

  test('should scan valid tag successfully', async ({ page }) => {
    // Generate valid UUID (or use a known test UUID)
    const testUUID = '550e8400-e29b-41d4-a716-446655440000';
    
    // Enter valid UUID
    await page.locator('input[type="text"]').fill(testUUID);
    
    // Submit form
    await page.locator('button[type="submit"]').click();
    
    // Should show loading state
    await expect(page.locator('[role="status"]')).toContainText(/loading|scanning/i);
    
    // Wait for results (max 5 seconds)
    await page.waitForSelector('[data-testid="scan-result"]', { timeout: 5000 });
    
    // Verify results are displayed
    const result = page.locator('[data-testid="scan-result"]');
    await expect(result).toBeVisible();
    
    // Should show scan count
    await expect(result).toContainText(/scan.*count|times.*scanned/i);
    
    // Should show product information
    await expect(result).toContainText(/product|item|name/i);
  });

  test('should handle antifraud blocking', async ({ page }) => {
    // Use a UUID known to trigger antifraud (in test environment)
    const blockedUUID = '00000000-0000-0000-0000-000000000001';
    
    // Enter blocked UUID
    await page.locator('input[type="text"]').fill(blockedUUID);
    await page.locator('button[type="submit"]').click();
    
    // Should show blocked message
    await expect(page.locator('[role="alert"]')).toContainText(/blocked|suspicious|try.*later/i);
  });

  test('should handle network errors gracefully', async ({ page, context }) => {
    // Simulate network error
    await context.route('**/v1/scan/*', route => route.abort('failed'));
    
    // Try to scan
    const testUUID = '550e8400-e29b-41d4-a716-446655440000';
    await page.locator('input[type="text"]').fill(testUUID);
    await page.locator('button[type="submit"]').click();
    
    // Should show error message
    await expect(page.locator('[role="alert"]')).toContainText(/error|failed|try.*again/i);
  });

  test('should display scan history (if authenticated)', async ({ page }) => {
    // Mock authentication
    await page.evaluate(() => {
      document.cookie = 'auth_token=mock_token_for_testing; path=/';
    });
    
    // Navigate to history page
    await page.goto('/history');
    
    // Should show scan history
    await expect(page.locator('[data-testid="scan-history"]')).toBeVisible();
    
    // Should show at least one scan
    const historyItems = page.locator('[data-testid="history-item"]');
    await expect(historyItems.first()).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Verify mobile layout
    const form = page.locator('form');
    await expect(form).toBeVisible();
    
    // Input should be full width on mobile
    const input = page.locator('input[type="text"]');
    const inputBox = await input.boundingBox();
    expect(inputBox?.width).toBeGreaterThan(300); // At least 80% of 375px
  });

  test('should handle rapid consecutive scans', async ({ page }) => {
    const testUUID = '550e8400-e29b-41d4-a716-446655440000';
    const input = page.locator('input[type="text"]');
    const submitBtn = page.locator('button[type="submit"]');
    
    // Scan 3 times rapidly
    for (let i = 0; i < 3; i++) {
      await input.fill(testUUID);
      await submitBtn.click();
      await page.waitForTimeout(500); // Small delay between scans
    }
    
    // Should handle all requests without errors
    await expect(page.locator('[role="alert"][aria-live="polite"]')).not.toBeVisible();
  });

  test('should respect rate limiting', async ({ page }) => {
    const testUUID = '550e8400-e29b-41d4-a716-446655440000';
    const input = page.locator('input[type="text"]');
    const submitBtn = page.locator('button[type="submit"]');
    
    // Scan many times rapidly to trigger rate limit
    for (let i = 0; i < 70; i++) {
      await input.fill(testUUID);
      await submitBtn.click();
      await page.waitForTimeout(100);
    }
    
    // Should show rate limit error
    await expect(page.locator('[role="alert"]')).toContainText(/rate.*limit|too.*many/i);
  });
});

test.describe('Consumer Scan - Accessibility', () => {
  test('should be keyboard accessible', async ({ page }) => {
    await page.goto('/scan');
    
    // Tab to input
    await page.keyboard.press('Tab');
    await expect(page.locator('input[type="text"]')).toBeFocused();
    
    // Type UUID
    await page.keyboard.type('550e8400-e29b-41d4-a716-446655440000');
    
    // Tab to submit button
    await page.keyboard.press('Tab');
    await expect(page.locator('button[type="submit"]')).toBeFocused();
    
    // Submit with Enter
    await page.keyboard.press('Enter');
    
    // Should submit successfully
    await expect(page.locator('[data-testid="scan-result"]')).toBeVisible({ timeout: 5000 });
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/scan');
    
    // Input should have label
    const input = page.locator('input[type="text"]');
    await expect(input).toHaveAttribute('aria-label', /tag.*id/i);
    
    // Form should have accessible name
    const form = page.locator('form');
    await expect(form).toHaveAttribute('aria-label', /scan|verify/i);
    
    // Alerts should have role="alert"
    const alerts = page.locator('[role="alert"]');
    if (await alerts.count() > 0) {
      await expect(alerts.first()).toHaveAttribute('role', 'alert');
    }
  });
});

test.describe('Consumer Scan - Performance', () => {
  test('should load quickly', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/scan');
    const loadTime = Date.now() - startTime;
    
    // Page should load in < 2 seconds
    expect(loadTime).toBeLessThan(2000);
  });

  test('should show results quickly', async ({ page }) => {
    await page.goto('/scan');
    
    const testUUID = '550e8400-e29b-41d4-a716-446655440000';
    await page.locator('input[type="text"]').fill(testUUID);
    
    const startTime = Date.now();
    await page.locator('button[type="submit"]').click();
    await page.waitForSelector('[data-testid="scan-result"]', { timeout: 5000 });
    const responseTime = Date.now() - startTime;
    
    // Results should appear in < 1 second (P95 < 100ms + network + render)
    expect(responseTime).toBeLessThan(1000);
  });
});
