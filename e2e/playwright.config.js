// @ts-check
const { defineConfig } = require('@playwright/test');

/**
 * Runs against the live production URL by default. Override with
 * BASE_URL=http://localhost:5000 to test a local instance instead.
 *
 * Render's free tier can take 30-70s to wake from a cold start and
 * individual requests are genuinely slower than a paid tier (shared
 * CPU) -- timeouts here are set generously on purpose so a slow-but-
 * working response doesn't get misreported as a failure.
 */
module.exports = defineConfig({
  testDir: './tests',
  timeout: 60000,
  expect: { timeout: 15000 },
  fullyParallel: false, // sequential: avoid tripping the free-tier instance into a health-check-timeout restart
  workers: 1,
  retries: 1,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'report' }]],
  use: {
    baseURL: process.env.BASE_URL || 'https://smart-port-backend.onrender.com',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    navigationTimeout: 30000,
    actionTimeout: 15000,
  },
});
