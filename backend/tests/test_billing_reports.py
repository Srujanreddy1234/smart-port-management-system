from datetime import datetime, timedelta


def _make_ship(client, headers, ship_id="SH-BILL-1"):
    res = client.post("/api/v1/ships", json={
        "ship_id": ship_id, "name": "MV Billing Test",
        "vessel_type": "Container Ship", "flag": "India",
    }, headers=headers)
    return res.get_json()["data"]["id"]


def test_invoice_lifecycle(client, admin_headers):
    ship_id = _make_ship(client, admin_headers)
    now = datetime.utcnow()
    res = client.post("/api/v1/billing", json={
        "ship_id": ship_id,
        "billing_period_start": now.isoformat(),
        "billing_period_end": (now + timedelta(days=1)).isoformat(),
        "due_date": (now + timedelta(days=30)).isoformat(),
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()
    invoice_id = res.get_json()["data"]["id"]

    res = client.post(f"/api/v1/billing/{invoice_id}/lines", json={
        "category": "Berth Usage Fee", "description": "Berth fee", "quantity": 1,
        "unit": "day", "unit_price": 5000,
    }, headers=admin_headers)
    assert res.status_code in (200, 201), res.get_json()

    res = client.get("/api/v1/billing/stats", headers=admin_headers)
    assert res.status_code == 200

    res = client.post(f"/api/v1/billing/{invoice_id}/pay", json={
        "amount": 5000, "payment_method": "Bank Transfer"
    }, headers=admin_headers)
    assert res.status_code == 200, res.get_json()


def test_generate_berth_invoice(client, admin_headers):
    ship_id = _make_ship(client, admin_headers, "SH-BILL-2")
    res = client.post("/api/v1/berths", json={
        "berth_id": "BTH-BILL-1", "name": "Billing Berth", "code": "BB1",
    }, headers=admin_headers)
    berth_id = res.get_json()["data"]["id"]

    now = datetime.utcnow()
    res = client.post("/api/v1/billing/generate-berth-invoice", json={
        "ship_id": ship_id, "berth_id": berth_id,
        "billing_period_start": now.isoformat(),
        "billing_period_end": (now + timedelta(days=2)).isoformat(),
    }, headers=admin_headers)
    assert res.status_code in (200, 201), res.get_json()


def test_reports_endpoints(client, admin_headers):
    res = client.get("/api/v1/reports/ship-traffic?days=30", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/reports/container-throughput?days=30", headers=admin_headers)
    assert res.status_code == 200
    assert "loaded" in res.get_json()["data"]

    res = client.get("/api/v1/reports/dashboard-summary", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/reports/port-traffic-annual", headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["granularity"] == "annual"


def test_container_throughput_loaded_count_is_correct(client, admin_headers):
    client.post("/api/v1/containers", json={
        "container_id": "CNT-LOADED-1", "container_type": "20ft", "status": "Loaded",
    }, headers=admin_headers)
    client.post("/api/v1/containers", json={
        "container_id": "CNT-EMPTY-1", "container_type": "20ft", "status": "Empty",
    }, headers=admin_headers)

    res = client.get("/api/v1/reports/container-throughput?days=30", headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["loaded"] == 1
