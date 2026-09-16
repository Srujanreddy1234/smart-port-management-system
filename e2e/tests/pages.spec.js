const { test, expect } = require('@playwright/test');
const { login, ROLES } = require('./helpers');

// Every page a Super Admin can reach must load without a hard failure
// and without throwing JS errors into the console. This is the same
// check that previously caught the invisible table-text CSS bug, the
// N+1 booking query, and the 403-spamming Store.init() bug -- it stays
// in the suite so those classes of regression can't come back quietly.
const PAGES = [
  'dashboard.html', 'ships.html', 'containers.html', 'trucks.html',
  'berths.html', 'gates.html', 'security.html', 'maintenance.html',
  'environment.html', 'billing.html', 'reports.html', 'profile.html', 'admin.html',
];

test.describe('Every page loads cleanly as Super Admin', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, ROLES.superAdmin);
  });

  for (const path of PAGES) {
    test(`${path} loads with no console/page errors`, async ({ page }) => {
      const errors = [];
      page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
      page.on('pageerror', (err) => errors.push(String(err)));

      const resp = await page.goto(`/${path}`, { waitUntil: 'domcontentloaded' });
      expect(resp.status(), `${path} should return 200`).toBe(200);

      // Give the page's own data-loading calls time to finish against
      // Supabase over the network -- these are genuinely a few seconds
      // on the free tier, not a bug.
      await page.waitForTimeout(5000);

      expect(errors, `${path} produced console/page errors: ${JSON.stringify(errors)}`).toEqual([]);
    });
  }
});
