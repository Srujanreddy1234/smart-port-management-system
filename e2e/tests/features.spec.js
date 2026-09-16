const { test, expect } = require('@playwright/test');
const { login, ROLES } = require('./helpers');

test.describe('Key features actually return real data', () => {
  test('AQI forecast returns a real ML prediction, not a placeholder', async ({ page, request, baseURL }) => {
    await login(page, ROLES.superAdmin);
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const res = await request.get(`${baseURL}/api/v1/environment/air-quality/forecast`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.data.available).toBe(true);
    expect(body.data.is_ml_prediction).toBe(true);
    expect(typeof body.data.predicted_aqi).toBe('number');
    // The model's own reported accuracy should beat a naive
    // "tomorrow = today" baseline -- if it doesn't, the model isn't
    // actually adding value.
    expect(body.data.model_metrics.model.mae).toBeLessThan(body.data.model_metrics.persistence_baseline.mae);
  });

  test('dashboard KPIs reflect real counts, not zeros', async ({ page, request, baseURL }) => {
    await login(page, ROLES.superAdmin);
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const res = await request.get(`${baseURL}/api/v1/dashboard/kpis`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.data.total_ships.value).toBeGreaterThan(0);
    expect(body.data.total_containers.value).toBeGreaterThan(0);
  });

  test('gate recommendation is computed live, not hardcoded to the same gate', async ({ page, request, baseURL }) => {
    await login(page, ROLES.superAdmin);
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    const res = await request.get(`${baseURL}/api/v1/gates/recommend`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.data.available).toBe(true);
    expect(body.data.recommended_gate.live).toHaveProperty('congestion');
    expect(body.data.recommended_gate.live).toHaveProperty('trucks_at_gate');
  });
});
