const { test, expect } = require('@playwright/test');
const { login, ROLES } = require('./helpers');

test.describe('Gate Routing & Time Slots', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, ROLES.truck);
    await page.goto('/gates.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(6000); // real Supabase round-trips for congestion + slots
  });

  test('shows live gate cards and a recommendation', async ({ page }) => {
    const gateCards = page.locator('.gate-card');
    await expect(gateCards).toHaveCount(4, { timeout: 20000 });
    await expect(page.locator('#recommendGateName')).not.toContainText('Loading...', { timeout: 20000 });
  });

  test('a truck operator can book a slot and see it in My Bookings, then cancel it', async ({ page, request, baseURL }) => {
    const openSlots = page.locator('.slot-btn:not([disabled])');
    await expect(openSlots.first()).toBeVisible({ timeout: 20000 });
    await openSlots.first().click();
    await page.waitForTimeout(500);
    await expect(page.locator('#bookSlotModal')).toBeVisible();

    await page.fill('#bsTruck', 'TN-E2E-TEST');
    await page.click('button[onclick="submitBooking()"]');
    await page.waitForTimeout(6000);

    await expect(page.locator('body')).toContainText('booked successfully');
    await expect(page.locator('#bookingsTableBody')).toContainText('TN-E2E-TEST');

    // Clean up via API regardless of UI cancel-button state, so this
    // test never leaves a live booking behind.
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const list = await request.get(`${baseURL}/api/v1/gates/bookings?mine=true&upcoming=false`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await list.json();
    const created = body.data.items.find((b) => b.truck_number === 'TN-E2E-TEST' && b.status === 'Booked');
    expect(created, 'the booking just made should be findable via the API').toBeTruthy();
    const cancel = await request.post(`${baseURL}/api/v1/gates/bookings/${created.id}/cancel`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(cancel.ok()).toBeTruthy();
  });

  test('a truck operator cannot see the "Manage Gates" action', async ({ page }) => {
    await expect(page.locator('#manageGatesBtn')).toBeHidden();
  });
});
