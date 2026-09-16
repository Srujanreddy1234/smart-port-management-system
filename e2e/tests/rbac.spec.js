const { test, expect } = require('@playwright/test');
const { login, ROLES } = require('./helpers');

// Confirms role restriction is a real server-side boundary, not just a
// hidden sidebar link -- hitting the API directly, bypassing the UI
// entirely.
test.describe('RBAC is enforced server-side', () => {
  test('Truck Operator cannot read the users list', async ({ page, request, baseURL }) => {
    await login(page, ROLES.truck);
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const res = await request.get(`${baseURL}/api/v1/users`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(403);
  });

  test('Truck Operator cannot create a gate', async ({ page, request, baseURL }) => {
    await login(page, ROLES.truck);
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const res = await request.post(`${baseURL}/api/v1/gates`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { gate_code: 'GATE-RBAC-TEST', name: 'Should be rejected', gate_type: 'General / Mixed' },
    });
    expect(res.status()).toBe(403);
  });

  test('Public role cannot book a gate slot (read-only access)', async ({ page, request, baseURL }) => {
    await login(page, ROLES.public);
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const res = await request.post(`${baseURL}/api/v1/gates/bookings`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        gate_id: 1, purpose: 'Container Pickup',
        slot_start: new Date(Date.now() + 86400000).toISOString(),
      },
    });
    expect(res.status()).toBe(403);
  });

  test('Truck Operator sidebar does not show Admin/Security/Billing', async ({ page }) => {
    await login(page, ROLES.truck);
    // The sidebar is populated by JS after login redirects, not present
    // in the initial HTML -- wait for it rather than racing it.
    await page.waitForSelector('.sidebar-nav a', { timeout: 15000 });
    const navText = await page.locator('.sidebar-nav').innerText();
    expect(navText).not.toMatch(/Admin Panel/i);
    expect(navText).not.toMatch(/Security/i);
    expect(navText).not.toMatch(/Billing/i);
    expect(navText).toMatch(/Gate Routing/i);
  });

  test('Super Admin sidebar shows everything', async ({ page }) => {
    await login(page, ROLES.superAdmin);
    await page.waitForSelector('.sidebar-nav a', { timeout: 15000 });
    const navText = await page.locator('.sidebar-nav').innerText();
    expect(navText).toMatch(/Admin Panel/i);
    expect(navText).toMatch(/Security/i);
    expect(navText).toMatch(/Billing/i);
    expect(navText).toMatch(/Gate Routing/i);
  });
});
