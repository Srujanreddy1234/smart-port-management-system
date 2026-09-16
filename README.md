# AI PORT — Smart Port Management System

A digital command center for Thoothukudi (V.O. Chidambaranar) Port — real-time
operations, environmental monitoring, security, maintenance, billing, and a
gate congestion routing system for truck drivers — built on real historical
weather/air-quality/marine data and a real machine-learning forecast, not
placeholder numbers.

**Live site:** https://smart-port-backend.onrender.com

## What this is

A role-based operations platform for a container port, covering:

- **Ship, container, truck, and berth management** — full CRUD, live status,
  KPIs, and charts driven by the real database, not mock data.
- **Gate Routing & Time Slots** — a Truck Appointment System (TAS): live
  per-gate congestion computed from real traffic, a "best gate right now"
  recommendation, and bookable 30-minute arrival slots so drivers know when
  to come instead of everyone converging on one gate at once. This is the
  standard, industry-proven fix for the truck-queueing problem real
  container terminals have, adapted for this port.
- **Environmental monitoring** — weather, air quality, marine, noise, and
  emissions readings imported from real historical sources (ERA5 reanalysis,
  CAMS reanalysis, Open-Meteo Marine), plus a trained RandomForestRegressor
  model that forecasts AQI 24 hours ahead (MAE 9.40 vs. a persistence
  baseline MAE of 11.83 — a genuine, measured improvement, not a fabricated
  metric).
- **Security, maintenance, billing, and reporting** modules with real
  role-based access control.
- **9 distinct roles** (Super Admin, Admin, Port Supervisor, Port Staff,
  Customs Officer, Shipping Company, Truck Operator, Customer, Public), each
  scoped to only the features and data that role actually needs — verified
  end to end, not just hidden in the sidebar.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Flask (app-factory pattern), SQLAlchemy, Flask-Migrate/Alembic, Flask-JWT-Extended, Marshmallow |
| Database | PostgreSQL (Supabase, free tier) |
| ML | scikit-learn (RandomForestRegressor), trained on real historical air-quality data |
| Frontend | Vanilla HTML/CSS/JS (no framework), Chart.js, Bootstrap 5 for layout primitives |
| Hosting | Render (Free Web Service), gunicorn + gthread workers |
| CI/keep-alive | GitHub Actions |

No paid infrastructure — this runs entirely on free tiers.

## Local development

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY
flask db upgrade
flask seed-data         # idempotent: seeds roles, permissions, demo users, gates
python ../datasets/scripts/import_to_database.py   # real historical weather/AQ/marine data
python ml/train_aqi_forecast.py                    # trains the AQI forecast model
flask run
```

Then open `http://localhost:5000` — the Flask app serves the frontend
directly (see `serve_frontend` in `backend/app/__init__.py`).

Run the test suite with `pytest tests/` from `backend/` (49 tests, in-memory
SQLite, no external services required).

## Deployment

- **Database:** Supabase Free PostgreSQL. Migrations are managed with
  Alembic (`flask db upgrade`) — never edit the schema by hand.
- **Hosting:** Render Free Web Service, `gunicorn wsgi:app --workers 2
  --worker-class gthread --threads 4`. Required env vars: `SECRET_KEY`,
  `JWT_SECRET_KEY`, `DATABASE_URL`, `SEED_ADMIN_PASSWORD`, `CORS_ORIGINS`,
  `FRONTEND_URL`, `FLASK_ENV=production`, `FLASK_APP=wsgi.py`,
  `PYTHON_VERSION=3.11.9` (pins the runtime to one with prebuilt wheels for
  scikit-learn/pandas — Render's default Python has none).
- **Keep-alive:** `.github/workflows/keep-alive.yml` pings `/health` every
  ~7 minutes (deliberately off round-number marks, since GitHub's own docs
  warn scheduled runs are most likely to be delayed right at `:00`) to keep
  Render's free tier from spinning down between visits. This is a
  best-effort mitigation, not a guarantee — GitHub's free scheduler can
  still occasionally miss a tick.

## Architecture notes worth knowing

- **RBAC is enforced on the backend**, not just hidden in the frontend nav —
  every API route checks `has_permission()` server-side. The frontend nav
  (`js/config.js`'s `ROLE_NAV_ITEMS`/`ROLE_PERMISSIONS`) mirrors this for UX
  but isn't the actual security boundary.
- **Identifier fields are format-validated**, not free text — ship IDs,
  container IDs, truck numbers, license plates, gate codes, etc. all go
  through `backend/app/utils/validators.py`, matching the real conventions
  already used in the data (uppercase alphanumeric with hyphens; Indian
  vehicle registration format for plates). Invalid input is rejected with a
  field-specific message, surfaced in the UI as a red-bordered input with an
  inline error (`App.showFieldError`/`applyFieldErrors` in `js/app.js`), not
  a generic toast.
- **Gate congestion is always computed live** from real data (trucks
  currently at a gate + how full upcoming booking slots are) — never a
  stored or fabricated number.
- **The AQI forecast model is loaded once at server startup**
  (`ml/predict_aqi.preload()`), not lazily on whichever user's request
  happens to hit it first — this used to cause a ~19-second stall for a
  random user right after a deploy.
- **`import_manifest.json`** (`datasets/processed/`) documents exactly which
  years of which datasets were imported and why, including years explicitly
  excluded for incomplete source coverage — no fabricated historical data.

## Demo accounts

All nine seeded roles use the password in the `SEED_ADMIN_PASSWORD`
environment variable (never committed). Emails follow `<role>@smartport.gov.in`,
e.g. `superadmin@smartport.gov.in`, `truck@smartport.gov.in`.
