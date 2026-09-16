const { test, expect } = require('@playwright/test');
const { login, ROLES } = require('./helpers');

test.describe('Authentication', () => {
  test('login page loads and has no demo credentials exposed', async ({ page }) => {
    await page.goto('/login.html', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/AI PORT/);
    // Regression guard: a "Quick access demo (password: admin123)" panel
    // used to ship on this page and always failed silently once real
    // random passwords were introduced.
    await expect(page.locator('body')).not.toContainText('admin123');
  });

  test('rejects an invalid password', async ({ page }) => {
    await page.goto('/login.html', { waitUntil: 'domcontentloaded' });
    await page.fill('#email', ROLES.superAdmin);
    await page.fill('#password', 'definitely-not-the-real-password');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);
    // Should still be on the login page -- a real backend rejection, not
    // a client-side check that happens to look right.
    expect(page.url()).toContain('login.html');
  });

  test('rejects an unregistered email', async ({ page }) => {
    await page.goto('/login.html', { waitUntil: 'domcontentloaded' });
    await page.fill('#email', 'nobody-registered@example.com');
    await page.fill('#password', 'whatever123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(4000);
    expect(page.url()).toContain('login.html');
  });

  test('logs in as super admin and lands on a real dashboard', async ({ page }) => {
    await login(page, ROLES.superAdmin);
    await expect(page).toHaveURL(/dashboard\.html|\/$/);
    await page.waitForFunction(
      () => document.getElementById('kpiShips')?.textContent !== '--',
      { timeout: 30000 }
    );
    const shipsCount = await page.locator('#kpiShips').textContent();
    expect(Number(shipsCount.replace(/,/g, ''))).toBeGreaterThan(0);
  });

  test('unauthenticated API access is rejected', async ({ request, baseURL }) => {
    const res = await request.get(`${baseURL}/api/v1/gates`);
    expect(res.status()).toBe(401);
  });
});
