# End-to-end tests

Real Playwright tests that run against the actual deployed site (or a
local instance) as a real browser would — login, click through every
page, create and clean up real records, and verify RBAC is enforced by
the server, not just hidden in the UI.

## Setup

```bash
cd e2e
npm install
npx playwright install chromium
```

## Running

```bash
E2E_PASSWORD=<the SEED_ADMIN_PASSWORD value> npx playwright test
```

Targets the live production URL by default. To run against a local
instance instead:

```bash
BASE_URL=http://localhost:5000 E2E_PASSWORD=<...> npx playwright test
```

View the HTML report after a run with `npx playwright show-report`.

## What's covered

- `auth.spec.js` — login/logout, invalid credentials rejected, unauthenticated API access rejected
- `pages.spec.js` — every page loads with zero console/page errors
- `crud.spec.js` — real create → appears in the list → delete cycle for ships/containers, plus the identifier format validation (red-bordered field, rejects malformed/lowercase IDs)
- `gates.spec.js` — the gate routing feature: live congestion, booking a real slot, seeing it in My Bookings, cleanup
- `rbac.spec.js` — role restrictions enforced server-side, not just in the sidebar
- `features.spec.js` — the AQI forecast and dashboard KPIs return real computed data, not placeholders

Every test that creates data cleans it up via the API at the end — this
suite must never leave test records in the production database.

## Notes

- Runs sequentially (`workers: 1`), not in parallel — the free-tier
  instance has very limited CPU, and running these in parallel can trip
  Render's health check into restarting the service mid-suite.
- Timeouts are generous on purpose. A slow-but-working response from a
  free-tier cold start or Supabase network hop is not a bug.
