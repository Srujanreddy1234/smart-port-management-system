const { test, expect } = require('@playwright/test');
const { login, ROLES } = require('./helpers');

// Runs a real create -> appears in list -> delete cycle against the
// live database, plus the format-validation UI added after a real
// production record was found saved as lowercase ("cont-100199").
// Every record this suite creates is deleted at the end -- it must
// never leave test data behind in production.

test.describe('Ship registration', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, ROLES.superAdmin);
    await page.goto('/ships.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
  });

  test('rejects a malformed Ship ID with an inline red-bordered error', async ({ page }) => {
    await page.evaluate(() => showRegisterShipModal());
    await page.fill('#rsShipId', 'not a valid id!!');
    await page.fill('#rsName', 'E2E Reject Test');
    await page.click('button[onclick="submitRegisterShip()"]');
    await page.waitForTimeout(500);

    await expect(page.locator('#rsShipId')).toHaveClass(/is-invalid/);
    const border = await page.locator('#rsShipId').evaluate((el) => getComputedStyle(el).borderColor);
    expect(border).toBe('rgb(220, 53, 69)');
    // The modal must still be open -- nothing was actually submitted.
    await expect(page.locator('#registerShipModal')).toBeVisible();
  });

  test('registers a real ship, it appears in the list, then is cleaned up', async ({ page, request, baseURL }) => {
    const shipId = `SH-E2E-${Date.now()}`;
    await page.evaluate(() => showRegisterShipModal());
    await page.fill('#rsShipId', shipId);
    await page.fill('#rsName', 'E2E Test Vessel');
    await page.click('button[onclick="submitRegisterShip()"]');
    await page.waitForTimeout(6000);

    await expect(page.locator('body')).toContainText('registered successfully');
    // Fresh reload proves it actually persisted server-side, not just an
    // optimistic local UI update.
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);
    await page.fill('#shipSearch', shipId);
    await page.waitForTimeout(1500);
    await expect(page.locator('body')).toContainText(shipId);

    // Cleanup via API so this test never leaves data behind.
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const list = await request.get(`${baseURL}/api/v1/ships?search=${shipId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await list.json();
    const created = body.data.items.find((s) => s.ship_id === shipId);
    expect(created, 'created ship should be findable via the API').toBeTruthy();
    await request.delete(`${baseURL}/api/v1/ships/${created.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  });
});

test.describe('Container registration', () => {
  test('typing a lowercase Container ID auto-uppercases as a real user types it', async ({ page }) => {
    // The real bug this guards: a container was saved to production as
    // "cont-100199" (lowercase) while every other record follows
    // "CONT-NNNN". page.fill() dispatches real input events, the same
    // as a user typing character by character, so this exercises the
    // actual oninput handler rather than bypassing it.
    await login(page, ROLES.superAdmin);
    await page.goto('/containers.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    await page.evaluate(() => showAddContainerModal());
    await page.fill('#acContainerId', 'cont-lowercase-test');
    await expect(page.locator('#acContainerId')).toHaveValue('CONT-LOWERCASE-TEST');
  });

  test('the backend independently rejects a lowercase Container ID even if a client bypasses the browser', async ({ page, request, baseURL }) => {
    await login(page, ROLES.superAdmin);
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const res = await request.post(`${baseURL}/api/v1/containers`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { container_id: `cont-e2e-${Date.now()}`, container_type: '20ft' },
    });
    expect(res.status()).toBe(400);
  });
});
