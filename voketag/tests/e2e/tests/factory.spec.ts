import { test, expect } from '@playwright/test';

/**
 * LOW ENHANCEMENT: E2E tests for factory/admin operations
 * 
 * Tests factory management workflows:
 * - Authentication
 * - Product creation
 * - Batch management
 * - CSV upload
 */

test.describe('Factory Authentication', () => {
  test('should show login page for unauthenticated users', async ({ page }) => {
    await page.goto('/factory');
    
    // Should redirect to login
    await expect(page).toHaveURL(/login/);
    
    // Verify login form
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Enter credentials (use test credentials)
    await page.locator('input[type="email"]').fill('test@voketag.com');
    await page.locator('input[type="password"]').fill('Test123!@#');
    
    // Submit
    await page.locator('button[type="submit"]').click();
    
    // Should redirect to factory dashboard
    await expect(page).toHaveURL(/factory|dashboard/);
    
    // Should show welcome message or user info
    await expect(page.locator('[data-testid="user-info"]')).toBeVisible();
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Enter invalid credentials
    await page.locator('input[type="email"]').fill('invalid@voketag.com');
    await page.locator('input[type="password"]').fill('WrongPassword');
    
    // Submit
    await page.locator('button[type="submit"]').click();
    
    // Should show error
    await expect(page.locator('[role="alert"]')).toContainText(/invalid|incorrect|wrong/i);
  });

  test('should validate email format', async ({ page }) => {
    await page.goto('/login');
    
    // Enter invalid email
    await page.locator('input[type="email"]').fill('not-an-email');
    await page.locator('input[type="password"]').fill('Password123');
    await page.locator('button[type="submit"]').click();
    
    // Should show validation error
    await expect(page.locator('[role="alert"]')).toContainText(/invalid.*email/i);
  });
});

test.describe('Factory Product Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('test@voketag.com');
    await page.locator('input[type="password"]').fill('Test123!@#');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/factory|dashboard/);
  });

  test('should create a new product', async ({ page }) => {
    // Navigate to products
    await page.goto('/factory/products');
    
    // Click "New Product" button
    await page.locator('button:has-text("New Product")').click();
    
    // Fill product form
    await page.locator('input[name="name"]').fill('Test Product E2E');
    await page.locator('input[name="sku"]').fill(`TEST-SKU-${Date.now()}`);
    await page.locator('textarea[name="description"]').fill('Created by E2E test');
    
    // Submit
    await page.locator('button[type="submit"]').click();
    
    // Should show success message
    await expect(page.locator('[role="alert"][aria-live="polite"]')).toContainText(/success|created/i);
    
    // Should redirect to product list
    await expect(page).toHaveURL(/products/);
    
    // Product should appear in list
    await expect(page.locator('text=Test Product E2E')).toBeVisible();
  });

  test('should validate product SKU format', async ({ page }) => {
    await page.goto('/factory/products/new');
    
    // Enter invalid SKU (lowercase, special chars)
    await page.locator('input[name="name"]').fill('Test Product');
    await page.locator('input[name="sku"]').fill('invalid sku @#$');
    await page.locator('button[type="submit"]').click();
    
    // Should show validation error
    await expect(page.locator('[role="alert"]')).toContainText(/invalid.*sku|alphanumeric/i);
  });

  test('should list all products with pagination', async ({ page }) => {
    await page.goto('/factory/products');
    
    // Should show product list
    await expect(page.locator('[data-testid="product-list"]')).toBeVisible();
    
    // Should show pagination controls
    const pagination = page.locator('[data-testid="pagination"]');
    await expect(pagination).toBeVisible();
    
    // Click next page
    await pagination.locator('button:has-text("Next")').click();
    
    // URL should update with page parameter
    await expect(page).toHaveURL(/page=2|skip=\d+/);
  });

  test('should search products', async ({ page }) => {
    await page.goto('/factory/products');
    
    // Enter search query
    const searchInput = page.locator('input[type="search"]');
    await searchInput.fill('Test Product');
    
    // Submit search
    await page.keyboard.press('Enter');
    
    // Results should be filtered
    await expect(page.locator('[data-testid="product-list"]')).toContainText(/test product/i);
  });

  test('should edit product', async ({ page }) => {
    await page.goto('/factory/products');
    
    // Click edit on first product
    await page.locator('[data-testid="product-item"]').first().locator('button:has-text("Edit")').click();
    
    // Should navigate to edit page
    await expect(page).toHaveURL(/products\/.*\/edit/);
    
    // Update name
    const nameInput = page.locator('input[name="name"]');
    await nameInput.clear();
    await nameInput.fill('Updated Product Name');
    
    // Submit
    await page.locator('button[type="submit"]').click();
    
    // Should show success
    await expect(page.locator('[role="alert"]')).toContainText(/success|updated/i);
  });

  test('should delete product', async ({ page }) => {
    await page.goto('/factory/products');
    
    // Click delete on first product
    await page.locator('[data-testid="product-item"]').first().locator('button:has-text("Delete")').click();
    
    // Should show confirmation dialog
    await expect(page.locator('[role="dialog"]')).toContainText(/confirm|delete|sure/i);
    
    // Confirm deletion
    await page.locator('[role="dialog"]').locator('button:has-text("Confirm")').click();
    
    // Should show success
    await expect(page.locator('[role="alert"]')).toContainText(/success|deleted/i);
  });
});

test.describe('Factory Batch Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('test@voketag.com');
    await page.locator('input[type="password"]').fill('Test123!@#');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/factory|dashboard/);
  });

  test('should create batch and upload CSV', async ({ page }) => {
    await page.goto('/factory/batches');
    
    // Click "New Batch"
    await page.locator('button:has-text("New Batch")').click();
    
    // Fill batch form
    await page.locator('input[name="name"]').fill(`Test Batch ${Date.now()}`);
    await page.locator('select[name="product_id"]').selectOption({ index: 1 }); // Select first product
    await page.locator('input[name="size"]').fill('100');
    
    // Submit
    await page.locator('button[type="submit"]').click();
    
    // Should show success
    await expect(page.locator('[role="alert"]')).toContainText(/success|created/i);
    
    // Should navigate to batch detail page
    await expect(page).toHaveURL(/batches\/[a-f0-9-]+/);
    
    // Upload CSV
    const csvContent = 'tag_id\n550e8400-e29b-41d4-a716-446655440000\n550e8400-e29b-41d4-a716-446655440001';
    const fileInput = page.locator('input[type="file"]');
    
    // Create a temporary file (in test environment)
    await fileInput.setInputFiles({
      name: 'test-tags.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent),
    });
    
    // Click upload
    await page.locator('button:has-text("Upload")').click();
    
    // Should show upload progress
    await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
    
    // Should show success after upload
    await expect(page.locator('[role="alert"]')).toContainText(/success|uploaded|processed/i, { timeout: 10000 });
  });

  test('should validate CSV file type', async ({ page }) => {
    await page.goto('/factory/batches/new');
    
    // Try to upload non-CSV file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('Not a CSV file'),
    });
    
    // Should show error
    await expect(page.locator('[role="alert"]')).toContainText(/invalid.*type|csv.*required/i);
  });

  test('should validate CSV file size', async ({ page }) => {
    await page.goto('/factory/batches/new');
    
    // Try to upload file > 10MB
    const largeContent = 'x'.repeat(11 * 1024 * 1024); // 11MB
    const fileInput = page.locator('input[type="file"]');
    
    await fileInput.setInputFiles({
      name: 'large.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(largeContent),
    });
    
    // Should show error
    await expect(page.locator('[role="alert"]')).toContainText(/too.*large|size.*limit/i);
  });
});

test.describe('Factory Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('test@voketag.com');
    await page.locator('input[type="password"]').fill('Test123!@#');
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/factory|dashboard/);
  });

  test('should display dashboard metrics', async ({ page }) => {
    await page.goto('/factory/dashboard');
    
    // Should show key metrics
    await expect(page.locator('[data-testid="metric-products"]')).toBeVisible();
    await expect(page.locator('[data-testid="metric-batches"]')).toBeVisible();
    await expect(page.locator('[data-testid="metric-scans"]')).toBeVisible();
    
    // Metrics should have values
    const productsMetric = await page.locator('[data-testid="metric-products"]').textContent();
    expect(productsMetric).toMatch(/\d+/);
  });

  test('should display recent activity', async ({ page }) => {
    await page.goto('/factory/dashboard');
    
    // Should show recent activity feed
    await expect(page.locator('[data-testid="recent-activity"]')).toBeVisible();
    
    // Should have at least one activity item
    const activityItems = page.locator('[data-testid="activity-item"]');
    await expect(activityItems.first()).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    await page.goto('/factory/dashboard');
    
    // Click logout button
    await page.locator('button:has-text("Logout")').click();
    
    // Should redirect to login page
    await expect(page).toHaveURL(/login/);
    
    // Should not be able to access protected pages
    await page.goto('/factory/products');
    await expect(page).toHaveURL(/login/);
  });
});
