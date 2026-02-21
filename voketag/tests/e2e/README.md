# E2E Tests with Playwright

## Overview

Comprehensive end-to-end tests for the VokeTag platform using Playwright.

**LOW ENHANCEMENT**: Browser-based testing for complete user journeys.

## Test Coverage

### Consumer Workflows (`tests/scan.spec.ts`)
- ✅ Scan page display
- ✅ Input validation (empty, invalid UUID)
- ✅ Successful scan flow
- ✅ Antifraud blocking
- ✅ Network error handling
- ✅ Scan history
- ✅ Mobile responsiveness
- ✅ Rate limiting
- ✅ Keyboard accessibility
- ✅ ARIA labels
- ✅ Performance (load time, response time)

### Factory Workflows (`tests/factory.spec.ts`)
- ✅ Authentication (login/logout)
- ✅ Product management (CRUD)
- ✅ Batch management
- ✅ CSV upload validation
- ✅ Dashboard metrics
- ✅ Recent activity
- ✅ Pagination
- ✅ Search

## Installation

```bash
cd tests/e2e
npm install
npx playwright install
```

## Running Tests

### All Tests
```bash
npm run test:e2e
```

### With Browser UI
```bash
npm run test:e2e:headed
```

### Debug Mode
```bash
npm run test:e2e:debug
```

### Interactive UI Mode
```bash
npm run test:e2e:ui
```

### Specific Browser
```bash
npm run test:e2e:chromium
npm run test:e2e:firefox
npm run test:e2e:webkit
```

### Mobile Tests Only
```bash
npm run test:e2e:mobile
```

### View Report
```bash
npm run test:e2e:report
```

## Configuration

Edit `playwright.config.ts`:

```typescript
export default defineConfig({
  // Test directory
  testDir: './tests',
  
  // Base URL (change for different environments)
  use: {
    baseURL: 'http://localhost:3000', // or staging/production URL
  },
  
  // Run local dev server
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
  },
});
```

## Environment Variables

Create `.env` file:

```bash
# Base URL for tests
BASE_URL=http://localhost:3000

# Test credentials
TEST_EMAIL=test@voketag.com
TEST_PASSWORD=Test123!@#

# Test UUID (for scan tests)
TEST_UUID=550e8400-e29b-41d4-a716-446655440000
```

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        working-directory: tests/e2e
        run: npm install
      
      - name: Install Playwright browsers
        working-directory: tests/e2e
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        working-directory: tests/e2e
        run: npm run test:e2e
        env:
          BASE_URL: ${{ secrets.STAGING_URL }}
          TEST_EMAIL: ${{ secrets.TEST_EMAIL }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
          retention-days: 30
```

## Test Data Management

### Fixtures

Create reusable test data in `tests/fixtures/`:

```typescript
// tests/fixtures/test-data.ts
export const testUsers = {
  factory: {
    email: 'test@voketag.com',
    password: 'Test123!@#',
  },
  admin: {
    email: 'admin@voketag.com',
    password: 'Admin123!@#',
  },
};

export const testProducts = [
  {
    name: 'Test Product 1',
    sku: 'TEST-001',
    description: 'E2E test product',
  },
];

export const testUUIDs = {
  valid: '550e8400-e29b-41d4-a716-446655440000',
  blocked: '00000000-0000-0000-0000-000000000001',
  notFound: 'ffffffff-ffff-ffff-ffff-ffffffffffff',
};
```

### Database Seeding

Before running tests, seed the database:

```bash
# Seed test database
npm run db:seed:test
```

## Page Object Model

For better maintainability, use Page Object Model:

```typescript
// tests/pages/ScanPage.ts
export class ScanPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/scan');
  }

  async scan(uuid: string) {
    await this.page.locator('input[type="text"]').fill(uuid);
    await this.page.locator('button[type="submit"]').click();
  }

  async waitForResults() {
    await this.page.waitForSelector('[data-testid="scan-result"]');
  }

  async getErrorMessage() {
    return await this.page.locator('[role="alert"]').textContent();
  }
}

// Usage in test
test('scan workflow', async ({ page }) => {
  const scanPage = new ScanPage(page);
  await scanPage.goto();
  await scanPage.scan('550e8400-e29b-41d4-a716-446655440000');
  await scanPage.waitForResults();
});
```

## Best Practices

### 1. Use Data Test IDs
```html
<div data-testid="scan-result">Result</div>
```

```typescript
await page.locator('[data-testid="scan-result"]')
```

### 2. Wait for Network Idle
```typescript
await page.goto('/scan', { waitUntil: 'networkidle' });
```

### 3. Use Auto-Waiting
```typescript
// Playwright automatically waits for elements
await page.locator('button').click(); // Waits for button to be visible and enabled
```

### 4. Isolate Tests
```typescript
test.beforeEach(async ({ page }) => {
  // Reset state before each test
  await page.goto('/');
});
```

### 5. Mock External APIs
```typescript
await page.route('**/api/external/**', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify({ mock: 'data' }),
  });
});
```

## Debugging

### Visual Debugging
```bash
npm run test:e2e:debug
```

### Screenshots on Failure
Automatically captured and saved to `test-results/`

### Videos
Recorded for failed tests, saved to `test-results/`

### Traces
View detailed traces with:
```bash
npx playwright show-trace trace.zip
```

## Performance Monitoring

### Lighthouse Integration

```typescript
import { test } from '@playwright/test';
import { playAudit } from 'playwright-lighthouse';

test('lighthouse audit', async ({ page }) => {
  await page.goto('/scan');
  
  await playAudit({
    page,
    thresholds: {
      performance: 90,
      accessibility: 95,
      'best-practices': 90,
      seo: 85,
    },
  });
});
```

## Troubleshooting

### Tests Failing Locally
1. Check if dev server is running: `http://localhost:3000`
2. Verify database has test data
3. Check environment variables in `.env`
4. Clear browser cache: `npx playwright clean`

### Tests Failing in CI
1. Check BASE_URL is correct
2. Verify secrets are configured
3. Ensure database migrations ran
4. Check network policies (firewalls)

### Slow Tests
1. Reduce parallel workers: `workers: 1`
2. Disable videos: `video: 'off'`
3. Use `--grep` to run specific tests
4. Optimize wait times

## Cost

**Infrastructure**: $0 (runs on CI/CD runners)  
**Time**: ~5-10 minutes per full test run  
**Maintenance**: 1-2 hours/month

## ROI

**Catches bugs before production**: Prevents 1 critical bug = $10,000+ saved  
**Confidence in deployments**: Reduces rollback risk  
**Documentation**: Tests serve as live documentation

---

**Estimated Effort**: 4-6 hours (initial setup) + 30 min per new workflow  
**Priority**: HIGH (prevents regressions)
