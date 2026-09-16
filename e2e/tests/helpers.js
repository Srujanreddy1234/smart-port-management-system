// Shared login helper. Never hardcode a real password here -- it comes
// from the E2E_PASSWORD env var at run time (the same value as the
// deployed SEED_ADMIN_PASSWORD), so this file is safe to commit.
async function login(page, email) {
  const password = process.env.E2E_PASSWORD;
  if (!password) {
    throw new Error('E2E_PASSWORD env var is not set -- see e2e/README.md');
  }
  await page.goto('/login.html', { waitUntil: 'domcontentloaded' });
  await page.fill('#email', email);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');
  await page.waitForURL((url) => !url.pathname.includes('login.html'), { timeout: 30000 });
}

const ROLES = {
  superAdmin: 'superadmin@smartport.gov.in',
  admin: 'admin@smartport.gov.in',
  supervisor: 'supervisor@smartport.gov.in',
  staff: 'staff@smartport.gov.in',
  customs: 'customs@smartport.gov.in',
  shipping: 'shipping@smartport.gov.in',
  truck: 'truck@smartport.gov.in',
  customer: 'customer@smartport.gov.in',
  public: 'public@smartport.gov.in',
};

module.exports = { login, ROLES };
