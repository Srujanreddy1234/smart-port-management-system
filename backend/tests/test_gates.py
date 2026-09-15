"""Gate congestion routing and time-slot booking (Truck Appointment
System). Covers the core driver flow plus the gates.book vs
gates.manage permission split -- a real bug caught during manual
testing where a truck operator could create gates and check in other
people's bookings before the permissions were split out."""
from datetime import datetime, timedelta
from tests.conftest import make_user, auth_headers
from app.models import UserRole


def _make_gate(db):
    from app.models import Gate, GateType, GateStatus
    gate = Gate(gate_code="GATE-T1", name="Test Gate", gate_type=GateType.CONTAINER,
                status=GateStatus.OPEN, capacity_per_hour=20)
    db.session.add(gate)
    db.session.commit()
    return gate


def _next_slot():
    dt = datetime.utcnow() + timedelta(days=1)
    return dt.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()


def test_list_gates_shows_live_congestion(client, db, admin_headers):
    _make_gate(db)
    res = client.get("/api/v1/gates", headers=admin_headers)
    assert res.status_code == 200
    gates = res.get_json()["data"]
    assert len(gates) == 1
    assert gates[0]["live"]["congestion"] == "Low"
    assert gates[0]["live"]["trucks_at_gate"] == 0


def test_recommend_picks_least_congested_open_gate(client, db, admin_headers):
    from app.models import Gate, GateType, GateStatus
    busy = Gate(gate_code="GATE-BUSY", name="Busy Gate", gate_type=GateType.CONTAINER,
                status=GateStatus.OPEN, capacity_per_hour=5)
    quiet = Gate(gate_code="GATE-QUIET", name="Quiet Gate", gate_type=GateType.GENERAL,
                 status=GateStatus.OPEN, capacity_per_hour=50)
    db.session.add_all([busy, quiet])
    db.session.commit()

    res = client.get("/api/v1/gates/recommend", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["available"] is True
    # With equal (zero) live traffic, the higher-capacity gate has more
    # headroom and should be ranked first.
    assert data["recommended_gate"]["gate_code"] == "GATE-QUIET"


def test_truck_operator_can_book_and_view_own_booking(client, db):
    make_user(db, "driver@test.local", UserRole.TRUCK_OPERATOR)
    headers = auth_headers(client, "driver@test.local")
    gate = _make_gate(db)

    res = client.post("/api/v1/gates/bookings", json={
        "gate_id": gate.id, "purpose": "Container Pickup",
        "truck_number": "TN-01-1234", "slot_start": _next_slot(),
    }, headers=headers)
    assert res.status_code == 201, res.get_json()
    booking_id = res.get_json()["data"]["id"]

    res = client.get("/api/v1/gates/bookings?mine=true&upcoming=false", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["total"] == 1
    assert res.get_json()["data"]["items"][0]["id"] == booking_id


def test_fully_booked_slot_is_rejected(client, db):
    make_user(db, "driver1@test.local", UserRole.TRUCK_OPERATOR)
    make_user(db, "driver2@test.local", UserRole.TRUCK_OPERATOR)
    gate = _make_gate(db)
    gate.capacity_per_hour = 2  # 1 slot/30min at this capacity
    db.session.commit()

    slot = _next_slot()
    h1 = auth_headers(client, "driver1@test.local")
    h2 = auth_headers(client, "driver2@test.local")

    res1 = client.post("/api/v1/gates/bookings", json={
        "gate_id": gate.id, "purpose": "Container Pickup", "slot_start": slot,
    }, headers=h1)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/gates/bookings", json={
        "gate_id": gate.id, "purpose": "Container Pickup", "slot_start": slot,
    }, headers=h2)
    assert res2.status_code == 400
    assert "fully booked" in res2.get_json()["message"].lower()


def test_truck_operator_cannot_create_gate_or_manage_others_bookings(client, db):
    """Regression test: gates.book (booking your own slot) must not
    also grant gates.manage (gate CRUD, checking in/completing anyone's
    booking) -- these were incorrectly merged into one permission when
    first built."""
    make_user(db, "driver@test.local", UserRole.TRUCK_OPERATOR)
    driver_headers = auth_headers(client, "driver@test.local")
    gate = _make_gate(db)

    res = client.post("/api/v1/gates", json={
        "gate_code": "GATE-NEW", "name": "Should Fail", "gate_type": "General / Mixed",
    }, headers=driver_headers)
    assert res.status_code == 403

    # Someone else's booking
    make_user(db, "other@test.local", UserRole.TRUCK_OPERATOR)
    other_headers = auth_headers(client, "other@test.local")
    res = client.post("/api/v1/gates/bookings", json={
        "gate_id": gate.id, "purpose": "Container Pickup", "slot_start": _next_slot(),
    }, headers=other_headers)
    other_booking_id = res.get_json()["data"]["id"]

    res = client.post(f"/api/v1/gates/bookings/{other_booking_id}/check-in", headers=driver_headers)
    assert res.status_code == 403

    res = client.post(f"/api/v1/gates/bookings/{other_booking_id}/cancel", headers=driver_headers)
    assert res.status_code == 403


def test_staff_can_manage_gates_and_any_booking(client, db, staff_headers):
    gate = _make_gate(db)
    res = client.put(f"/api/v1/gates/{gate.id}", json={"capacity_per_hour": 30}, headers=staff_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["capacity_per_hour"] == 30

    make_user(db, "driver3@test.local", UserRole.TRUCK_OPERATOR)
    driver_headers = auth_headers(client, "driver3@test.local")
    res = client.post("/api/v1/gates/bookings", json={
        "gate_id": gate.id, "purpose": "Container Pickup", "slot_start": _next_slot(),
    }, headers=driver_headers)
    booking_id = res.get_json()["data"]["id"]

    res = client.post(f"/api/v1/gates/bookings/{booking_id}/check-in", headers=staff_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "Checked In"

    res = client.post(f"/api/v1/gates/bookings/{booking_id}/complete", headers=staff_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "Completed"


def test_availability_reflects_bookings(client, db, admin_headers):
    make_user(db, "driver4@test.local", UserRole.TRUCK_OPERATOR)
    driver_headers = auth_headers(client, "driver4@test.local")
    gate = _make_gate(db)
    gate.capacity_per_hour = 2
    db.session.commit()

    slot = _next_slot()
    client.post("/api/v1/gates/bookings", json={
        "gate_id": gate.id, "purpose": "Container Pickup", "slot_start": slot,
    }, headers=driver_headers)

    date_str = slot.split("T")[0]
    res = client.get(f"/api/v1/gates/{gate.id}/availability?date={date_str}", headers=admin_headers)
    assert res.status_code == 200
    slots = res.get_json()["data"]["slots"]
    booked_slot = next(s for s in slots if s["slot_start"].startswith(slot[:16]))
    assert booked_slot["booked"] == 1
    assert booked_slot["available"] == 0
