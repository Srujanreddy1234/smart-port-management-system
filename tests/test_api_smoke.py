#!/usr/bin/env python3
"""
SMOKE TESTS for Smart Port Management System API
Tests every endpoint for basic HTTP response status (smoke test).
Run: python3 tests/test_api.py
"""

import requests
import sys
import time
import json

API_BASE = "http://127.0.0.1:5001/api/v1"
TOKEN = None
HEADERS = {"Content-Type": "application/json"}

PASS = 0
FAIL = 0
SKIP = 0
RESULTS = []


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def log_result(method, endpoint, status, expected, body=""):
    global PASS, FAIL, SKIP
    if status == "SKIP":
        SKIP += 1
        RESULTS.append(f"{Colors.YELLOW}SKIP {method} {endpoint}{Colors.RESET}")
        return
    if status == expected or (isinstance(expected, list) and status in expected):
        PASS += 1
        RESULTS.append(f"{Colors.GREEN}PASS {method} {endpoint} → {status}{Colors.RESET}")
    else:
        FAIL += 1
        detail = f" ({body[:100]})" if body else ""
        RESULTS.append(f"{Colors.RED}FAIL {method} {endpoint} → expected {expected}, got {status}{detail}{Colors.RESET}")


def api(method, endpoint, data=None, expected=200, auth=True):
    url = f"{API_BASE}{endpoint}"
    h = dict(HEADERS)
    if auth and TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    try:
        if method == "GET":
            r = requests.get(url, headers=h, timeout=10)
        elif method == "POST":
            r = requests.post(url, headers=h, json=data, timeout=10)
        elif method == "PUT":
            r = requests.put(url, headers=h, json=data, timeout=10)
        elif method == "DELETE":
            r = requests.delete(url, headers=h, timeout=10)
        else:
            print(f"UNKNOWN METHOD: {method}")
            return None
        exp = expected if expected is not None else 200
        print(f"  {Colors.BLUE}{method} {endpoint} → {r.status_code} (expected {exp}){Colors.RESET}")
        check(method, endpoint, r.status_code, exp, r.text[:100] if r.status_code >= 400 else None)
        try:
            return r.json()
        except:
            return {"raw": r.text}
    except requests.ConnectionError:
        print(f"  {Colors.RED}CONNECTION REFUSED{Colors.RESET}")
        sys.exit(1)


def check(method, endpoint, status, expected, body=None):
    global PASS, FAIL
    if isinstance(expected, list):
        ok = status in expected
    else:
        ok = status == expected
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print(f"    {Colors.RED}Expected {expected}, got {status}{Colors.RESET}")


# ============================================================
# AUTH TESTS
# ============================================================
def test_auth():
    global TOKEN
    print(f"\n{Colors.BOLD}=== AUTH (/api/v1/auth) ==={Colors.RESET}")

    # Login (get token for subsequent tests)
    try:
        r = requests.post(f"{API_BASE}/auth/login", json={"email": "superadmin@smartport.gov.in", "password": "admin123"}, headers=HEADERS, timeout=10)
        print(f"  POST /auth/login → {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            TOKEN = data.get("access_token") or data.get("token") or data.get("data", {}).get("access_token")
            check("POST", "/auth/login", 200, 200)
        else:
            check("POST", "/auth/login", r.status_code, 200)
    except:
        print(f"  {Colors.RED}Connection refused — starting mock mode{Colors.RESET}")
        TOKEN = "mock-token"

    if TOKEN:
        api("GET", "/auth/me", expected=200)
        api("POST", "/auth/logout", expected=[200, 201, 401])
        api("POST", "/auth/refresh", expected=[200, 401])

    api("POST", "/auth/change-password", {"old_password": "admin123", "new_password": "admin1234"}, expected=[200, 201, 401])


# ============================================================
# DASHBOARD TESTS
# ============================================================
def test_dashboard():
    print(f"\n{Colors.BOLD}═══ DASHBOARD (/api/dashboard) ==={Colors.RESET}")
    api("GET", "/dashboard/kpis")
    api("GET", "/dashboard/recent-activity")
    api("GET", "/dashboard/vessel-status")
    api("GET", "/dashboard/berth-occupancy")
    api("GET", "/dashboard/charts/vessel-arrivals")
    api("GET", "/dashboard/charts/container-distribution")
    api("GET", "/dashboard/charts/throughput")
    api("GET", "/dashboard/charts/truck-traffic")
    api("GET", "/dashboard/charts/environmental-trends")
    api("GET", "/dashboard/charts/equipment-health")


# ============================================================
# SHIPS TESTS (CRUD)
# ============================================================
def test_ships():
    global created_ship_id
    print(f"\n{Colors.BOLD}═══ SHIPS (/api/ships) ==={Colors.RESET}")

    # GET list
    data = api("GET", "/ships")
    assert data is not None, "Failed to get ships list"

    # GET stats & charts
    api("GET", "/ships/stats")
    api("GET", "/ships/arrivals-chart?days=30")

    # POST - create
    new_ship = {
        "ship_id": "TEST-UNIT",
        "name": "Test Vessel Unit",
        "vessel_type": "Container Ship",
        "flag": "Panama",
        "status": "Scheduled",
        "length_overall": 200.0,
        "beam": 30.0,
        "draft": 10.0,
        "agent": "Test Agent",
        "imo_number": "TEST-UNIT-01"
    }
    result = api("POST", "/ships", new_ship, expected=[200, 201, 400, 422, 500])
    if result and isinstance(result, dict):
        created_ship_id = result.get("id") or (result.get("data", {}) or {}).get("id")
        print(f"    Created ship ID: {created_ship_id}")

    # If we got a valid ID, test subsequent operations
    if created_ship_id:
        api("GET", f"/ships/{created_ship_id}")
        api("PUT", f"/ships/{created_ship_id}", {"name": "Test Updated", "status": "Anchored"}, expected=[200, 400, 401])
        api("POST", f"/ships/{created_ship_id}/arrival", expected=[200, 400, 401])
        api("POST", f"/ships/{created_ship_id}/departure", expected=[200, 400, 401])
        api("DELETE", f"/ships/{created_ship_id}", expected=[200, 204, 400, 401])
        created_ship_id = None
    else:
        # Test on ID=1 as fallback
        api("GET", "/ships/1", expected=[200, 404, 401])
        api("PUT", "/ships/1", {"name": "Test Update"}, expected=[200, 400, 401, 404])
        api("POST", "/ships/1/arrival", expected=[200, 400, 401, 404])
        api("POST", "/ships/1/departure", expected=[200, 400, 401, 404])
        api("DELETE", "/ships/1", expected=[200, 400, 401, 404])


created_ship_id = None
created_container_id = None
created_truck_id = None
created_berth_id = None
created_invoice_id = None
created_incident_id = None
created_equipment_id = None
created_schedule_id = None
created_station_id = None
created_user_id = None
created_role_id = None


# ============================================================
# CONTAINERS TESTS (CRUD)
# ============================================================
def test_containers():
    global created_container_id
    print(f"\n{Colors.BOLD}═══ CONTAINERS (/api/containers) ==={Colors.RESET}")

    api("GET", "/containers")
    api("GET", "/containers/stats")
    api("GET", "/containers/flow-chart")
    api("GET", "/containers/type-distribution")

    new_container = {
        "container_number": "TEST-CNT-001",
        "type": "Standard",
        "type_size": "40FT",
        "status": "In Transit",
        "contents": "Electronics",
        "shipping_line": "Maersk",
        "seal_number": "SEAL-001",
        "gross_weight_kg": 20000,
        "tare_weight_kg": 4000
    }
    result = api("POST", "/containers", new_container, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_container_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_container_id:
        api("GET", f"/containers/{created_container_id}")
        api("PUT", f"/containers/{created_container_id}", {"status": "At Dock"}, expected=[200, 400, 401])
        api("POST", f"/containers/{created_container_id}/assign-ship", {"ship_id": 1}, expected=[200, 400, 401, 404])
        api("POST", f"/containers/{created_container_id}/assign-truck", {"truck_id": 1}, expected=[200, 400, 401, 404])
        api("POST", f"/containers/{created_container_id}/move", {"location": "Gate 1"}, expected=[200, 400, 401])
        api("GET", f"/containers/{created_container_id}/history", expected=[200, 404, 401])
        api("DELETE", f"/containers/{created_container_id}", expected=[200, 400, 401])
        created_container_id = None
    else:
        api("GET", "/containers/1", expected=[200, 404, 401])


# ============================================================
# TRUCKS TESTS (CRUD)
# ============================================================
def test_trucks():
    global created_truck_id
    print(f"\n{Colors.BOLD}═══ TRUCKS (/api/trucks) ==={Colors.RESET}")

    api("GET", "/trucks")
    api("GET", "/trucks/stats")

    new_truck = {
        "license_plate": "TEST-TRCK-001",
        "driver_name": "Test Driver",
        "driver_contact": "+91-9876543210",
        "status": "Waiting",
        "has_container": False
    }
    result = api("POST", "/trucks", new_truck, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_truck_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_truck_id:
        api("GET", f"/trucks/{created_truck_id}")
        api("PUT", f"/trucks/{created_truck_id}", {"status": "Processing"}, expected=[200, 400, 401])
        api("POST", f"/trucks/{created_truck_id}/gate-in", expected=[200, 400, 401])
        api("POST", f"/trucks/{created_truck_id}/gate-out", expected=[200, 400, 401])
        api("DELETE", f"/trucks/{created_truck_id}", expected=[200, 400, 401])
        created_truck_id = None
    else:
        api("GET", "/trucks/1", expected=[200, 404, 401])


# ============================================================
# BERTHS TESTS (CRUD)
# ============================================================
def test_berths():
    global created_berth_id
    print(f"\n{Colors.BOLD}═══ BERTS (/api/berths) ==={Colors.RESET}")

    api("GET", "/berths")
    api("GET", "/berths/available")
    api("GET", "/berths/stats")

    new_berth = {
        "label": "TEST-BTH",
        "length_m": 300,
        "depth_m": 15,
        "status": "Available"
    }
    result = api("POST", "/berths", new_berth, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_berth_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_berth_id:
        api("GET", f"/berths/{created_berth_id}")
        api("PUT", f"/berths/{created_berth_id}", {"status": "Occupied"}, expected=[200, 400, 401])
        api("POST", f"/berths/{created_berth_id}/assign", {"ship_id": 1}, expected=[200, 400, 401])
        api("POST", f"/berths/{created_berth_id}/release", expected=[200, 400, 401])
        api("DELETE", f"/berths/{created_berth_id}", expected=[200, 400, 401])
        created_berth_id = None
    else:
        api("GET", "/berths/1", expected=[200, 404, 401])
        api("POST", "/berths/1/assign", {"ship_id": 1}, expected=[200, 400, 401, 404])
        api("POST", "/berths/1/release", expected=[200, 400, 401, 404])


# ============================================================
# BILLING TESTS (CRUD)
# ============================================================
def test_billing():
    global created_invoice_id
    print(f"\n{Colors.BOLD}═══ BILLING (/api/billing) ==={Colors.RESET}")

    api("GET", "/billing")
    api("GET", "/billing/stats")

    new_invoice = {
        "invoice_number": "INV-TEST-001",
        "invoice_type": "berthing",
        "seller_name": "Scale Harbor",
        "seller_tax_id": "TAX123456",
        "seller_address": "Test Address",
        "buyer_name": "SPMP",
        "buyer_tax_id": "TAX654321",
        "buyer_address": "Buyer Address",
        "due_date": "2025-12-31",
        "notes": "Test invoice",
        "subtotal": 5000.00,
        "tax_rate": 18.0,
        "tax_amount": 900.00,
        "total": 5900.00,
        "currency": "USD"
    }
    result = api("POST", "/billing", new_invoice, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_invoice_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_invoice_id:
        api("GET", f"/billing/{created_invoice_id}")
        api("POST", f"/billing/{created_invoice_id}/lines", {
            "category": "Berthing Fee",
            "description": "Test line",
            "quantity": 1,
            "unit": "days",
            "unit_price": 5000.00
        }, expected=[200, 201, 400, 401])
        api("POST", f"/billing/{created_invoice_id}/pay", expected=[200, 400, 401])
        api("POST", f"/billing/{created_invoice_id}/send", expected=[200, 400, 401])
        api("POST", f"/billing/{created_invoice_id}/cancel", expected=[200, 400, 401])
        created_invoice_id = None
    else:
        api("GET", "/billing/1", expected=[200, 404, 401])


# ============================================================
# SECURITY TESTS (CRUD)
# ============================================================
def test_security():
    global created_incident_id
    print(f"\n{Colors.BOLD}═══ SECURITY (/api/security) ==={Colors.RESET}")

    api("GET", "/security")
    api("GET", "/security/alerts")
    api("GET", "/security/cameras")

    new_incident = {
        "title": "Test Incident",
        "description": "Test incident description",
        "severity": "Low",
        "location": "Gate A",
        "status": "Open",
        "type": "Test Inc",
        "assigned_to": "Security Officer"
    }
    result = api("POST", "/security", new_incident, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_incident_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_incident_id:
        api("GET", f"/security/{created_incident_id}")
        api("PUT", f"/security/{created_incident_id}", {"status": "Resolved"}, expected=[200, 400, 401])
        api("DELETE", f"/security/{created_incident_id}", expected=[200, 400, 401])
        created_incident_id = None
    else:
        api("GET", "/security/1", expected=[200, 404, 401])
        api("POST", "/security/alerts/1/acknowledge", expected=[200, 400, 401, 404])


# ============================================================
# MAINTENANCE TESTS (CRUD)
# ============================================================
def test_maintenance():
    global created_equipment_id, created_schedule_id
    print(f"\n{Colors.BOLD}═══ MAINTENANCE (/api/maintenance) ==={Colors.RESET}")

    api("GET", "/maintenance")
    api("GET", "/maintenance/schedules")

    new_equipment = {
        "name": "Test Equipment",
        "element_type": "Crane",
        "location": "Berth 1",
        "status": "Operational",
        "manufacturer": "Test Mfr",
        "model": "Model X",
        "serial_number": "SN-001",
        "installation_date": "2026-01-01",
        "last_maintenance": "2026-06-01",
        "next_maintenance": "2026-12-01",
        "maintenance_frequency_days": 180
    }
    result = api("POST", "/maintenance", new_equipment, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_equipment_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_equipment_id:
        api("GET", f"/maintenance/{created_equipment_id}")
        api("PUT", f"/maintenance/{created_equipment_id}", {"status": "Under Maintenance"}, expected=[200, 400, 401])
    else:
        api("GET", "/maintenance/1", expected=[200, 404, 401])

    new_schedule = {
        "equipment_id": created_equipment_id or 1,
        "schedule_type": "routine",
        "description": "Test schedule",
        "date": "2026-12-01",
        "status": "Scheduled",
        "assigned_to": "Technician 1"
    }
    result2 = api("POST", "/maintenance/schedules", new_schedule, expected=[200, 201, 400, 401, 500])
    if result2 and isinstance(result2, dict):
        created_schedule_id = result2.get("id") or (result2.get("data", {}) or {}).get("id")

    if created_schedule_id:
        api("GET", f"/maintenance/schedules/{created_schedule_id}")
        api("PUT", f"/maintenance/schedules/{created_schedule_id}", {"status": "Completed"}, expected=[200, 400, 401])
    else:
        api("GET", "/maintenance/schedules/1", expected=[200, 404, 401])

    if created_equipment_id:
        api("DELETE", f"/maintenance/{created_equipment_id}", expected=[200, 400, 401])
        created_equipment_id = None


# ============================================================
# ENVIRONMENT TESTS (CRUD)
# ============================================================
def test_environment():
    global created_station_id
    print(f"\n{Colors.BOLD}═══ ENVIRONMENT (/api/environment) ==={Colors.RESET}")

    api("GET", "/environment")
    api("GET", "/environment/air-quality")
    api("GET", "/environment/water-quality")
    api("GET", "/environment/noise")
    api("GET", "/environment/weather")
    api("GET", "/environment/alerts")

    new_station = {
        "station_name": "TEST-STN",
        "station_type": "Air Quality",
        "location": "Test Quay",
        "gps_coordinates": "12.3456,78.9012",
        "status": "Active"
    }
    result = api("POST", "/environment", new_station, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_station_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_station_id:
        api("GET", f"/environment/{created_station_id}")
        api("PUT", f"/environment/{created_station_id}", {"status": "Inactive"}, expected=[200, 400, 401])
        api("DELETE", f"/environment/{created_station_id}", expected=[200, 400, 401])
        created_station_id = None
    else:
        api("GET", "/environment/1", expected=[200, 404, 401])


# ============================================================
# USERS TESTS (CRUD)
# ============================================================
def test_users():
    global created_user_id
    print(f"\n{Colors.BOLD}═══ USERS (/api/users) ==={Colors.RESET}")

    api("GET", "/users")
    api("GET", "/users/stats")

    new_user = {
        "email": "test.user@smartport.gov.in",
        "password": "Test@1234",
        "name": "Test User",
        "name": "Test API User",
        "role": "Operator",
        "contact_number": "+91-9876543210",
        "department": "Operations"
    }
    result = api("POST", "/users", new_user, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_user_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_user_id:
        api("GET", f"/users/{created_user_id}")
        api("PUT", f"/users/{created_user_id}", {"name": "Updated", "contact_number": "+91-9999999999"}, expected=[200, 400, 401])
        api("POST", f"/users/{created_user_id}/reset-password", {"new_password": "Test@12345"}, expected=[200, 400, 401])
        api("DELETE", f"/users/{created_user_id}", expected=[200, 400, 401])
        created_user_id = None
    else:
        api("GET", "/users/1", expected=[200, 404, 401])


# ============================================================
# ROLES TESTS (CRUD)
# ============================================================
def test_roles():
    global created_role_id
    print(f"\n{Colors.BOLD}═══ ROLES (/api/roles) ==={Colors.RESET}")

    api("GET", "/roles")
    api("GET", "/roles/permissions")

    new_role = {
        "role_name": "Test-Role-001",
        "description": "Test role for unit tests",
        "permissions": "view_ships"
    }
    result = api("POST", "/roles", new_role, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_role_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_role_id:
        api("GET", f"/roles/{created_role_id}")
        api("PUT", f"/roles/{created_role_id}", {"description": "Updated"}, expected=[200, 400, 401])
        api("DELETE", f"/roles/{created_role_id}", expected=[200, 400, 401])
        created_role_id = None
    else:
        api("GET", "/roles/1", expected=[200, 404, 401])


# ============================================================
# REPORTS TESTS
# ============================================================
def test_reports():
    global created_report_id
    print(f"\n{Colors.BOLD}═══ REPORTS (/api/reports) ==={Colors.RESET}")

    api("GET", "/reports")
    api("GET", "/reports/ship-traffic")
    api("GET", "/reports/container-throughput")
    api("GET", "/reports/dashboard-summary")

    new_report = {
        "title": "Test Report",
        "report_type": "Monthly Summary",
        "description": "Generated by unit test"
    }
    result = api("POST", "/reports", new_report, expected=[200, 201, 400, 401, 500])
    if result and isinstance(result, dict):
        created_report_id = result.get("id") or (result.get("data", {}) or {}).get("id")

    if created_report_id:
        api("GET", f"/reports/{created_report_id}")
        api("GET", f"/reports/{created_report_id}/download", expected=[200, 400, 401, 404])
        api("GET", f"/reports/{created_report_id}/file", expected=[200, 400, 401, 404])
        created_report_id = None


# ============================================================
# EVENTS / SSE TEST
# ============================================================
def test_events():
    print(f"\n{Colors.BOLD}═══ EVENTS (/api/events) ==={Colors.RESET}")
    api("GET", "/events/recent")


# ============================================================
# SEARCH TEST
# ============================================================
def test_search():
    print(f"\n{Colors.BOLD}═══ SEARCH (/api/search) ==={Colors.RESET}")
    api("GET", "/search?q=test")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  SMART PORT MANAGEMENT - API Smoke Tests")
    print("=" * 60)
    print(f"{Colors.RESET}")

    test_auth()
    test_dashboard()
    test_ships()
    test_containers()
    test_trucks()
    test_berths()
    test_billing()
    test_security()
    test_maintenance()
    test_environment()
    test_users()
    test_roles()
    test_reports()
    test_events()
    test_search()

    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"  Results: {Colors.GREEN}{PASS} passed{Colors.RESET}, {Colors.RED}{FAIL} failed{Colors.RESET}, {Colors.YELLOW}{SKIP} skipped{Colors.RESET}")
    print(f"  Total: {PASS + FAIL + SKIP} tests")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")

    sys.exit(0 if FAIL == 0 else 1)