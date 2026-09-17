from datetime import datetime, timedelta
from tests.conftest import make_user
from app.models import UserRole


def _make_ship(client, headers, ship_id, agent_email=None):
    payload = {
        "ship_id": ship_id, "name": "MV Security Test",
        "vessel_type": "Container Ship", "flag": "India",
    }
    if agent_email:
        payload["agent_email"] = agent_email
    res = client.post("/api/v1/ships", json=payload, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]["id"]


def _make_invoice(client, headers, ship_id):
    now = datetime.utcnow()
    res = client.post("/api/v1/billing", json={
        "ship_id": ship_id,
        "billing_period_start": now.isoformat(),
        "billing_period_end": (now + timedelta(days=1)).isoformat(),
        "due_date": (now + timedelta(days=30)).isoformat(),
    }, headers=headers)
    assert res.status_code == 201, res.get_json()
    return res.get_json()["data"]["id"]


def test_shipping_company_only_sees_own_invoices(client, db, admin_headers):
    own_ship = _make_ship(client, admin_headers, "SH-SEC-1", agent_email="agent@shippingco.test")
    other_ship = _make_ship(client, admin_headers, "SH-SEC-2", agent_email="other@shippingco.test")
    own_invoice_id = _make_invoice(client, admin_headers, own_ship)
    other_invoice_id = _make_invoice(client, admin_headers, other_ship)

    make_user(db, "agent@shippingco.test", UserRole.SHIPPING_COMPANY)
    from tests.conftest import auth_headers
    shipping_headers = auth_headers(client, "agent@shippingco.test")

    res = client.get("/api/v1/billing", headers=shipping_headers)
    assert res.status_code == 200
    ids = [inv["id"] for inv in res.get_json()["data"]["items"]]
    assert own_invoice_id in ids
    assert other_invoice_id not in ids

    res = client.get(f"/api/v1/billing/{own_invoice_id}", headers=shipping_headers)
    assert res.status_code == 200

    res = client.get(f"/api/v1/billing/{other_invoice_id}", headers=shipping_headers)
    assert res.status_code == 404


def test_global_search_hides_users_without_permission(client, db, admin_headers):
    make_user(db, "trucker@test.local", UserRole.TRUCK_OPERATOR)
    from tests.conftest import auth_headers
    truck_headers = auth_headers(client, "trucker@test.local")

    res = client.get("/api/v1/search?q=admin", headers=truck_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["users"] == []

    res = client.get("/api/v1/search?q=admin", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert isinstance(data["users"], list)


def test_sse_stream_requires_valid_token(client):
    res = client.get("/api/v1/events/stream")
    assert res.status_code == 401

    res = client.get("/api/v1/events/stream?token=not-a-real-token")
    assert res.status_code == 401


def test_sse_stream_accepts_valid_token_via_query_string(client, admin_headers):
    token = admin_headers["Authorization"].split(" ")[1]
    res = client.get(f"/api/v1/events/stream?token={token}")
    assert res.status_code == 200
    res.close()


def test_recent_events_requires_permission(client, db):
    make_user(db, "customer@test.local", UserRole.CUSTOMER)
    from tests.conftest import auth_headers
    customer_headers = auth_headers(client, "customer@test.local")

    res = client.get("/api/v1/events/recent", headers=customer_headers)
    assert res.status_code == 403


def test_report_file_download_requires_permission(client, db, admin_headers):
    res = client.post("/api/v1/reports", json={
        "title": "Test Report", "report_type": "Vessel Traffic", "format": "JSON",
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()
    report_id = res.get_json()["data"]["id"]

    make_user(db, "public@test.local", UserRole.PUBLIC)
    from tests.conftest import auth_headers
    public_headers = auth_headers(client, "public@test.local")

    res = client.get(f"/api/v1/reports/{report_id}/file", headers=public_headers)
    assert res.status_code == 403


def test_berths_read_requires_permission(client, db):
    make_user(db, "noaccess@test.local", UserRole.PUBLIC)
    from tests.conftest import auth_headers
    headers = auth_headers(client, "noaccess@test.local")

    res = client.get("/api/v1/berths", headers=headers)
    assert res.status_code == 403


def test_sort_by_rejects_non_column_values(client, admin_headers):
    res = client.get("/api/v1/ships?sort_by=__class__", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/berths?sort_by=nonexistent_evil_column", headers=admin_headers)
    assert res.status_code == 200
