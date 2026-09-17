"""CRUD smoke coverage for the main operational resources: ships, containers,
trucks, berths. Uses an admin (SUPER_ADMIN -> 'all' permission) so these
tests exercise the resource logic itself, not permission edge cases
(those are covered in test_rbac.py)."""


def test_ships_crud(client, admin_headers):
    res = client.post("/api/v1/ships", json={
        "ship_id": "SH-TEST-1", "name": "MV Test Carrier",
        "vessel_type": "Container Ship", "flag": "India",
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()
    ship_id = res.get_json()["data"]["id"]

    res = client.get(f"/api/v1/ships/{ship_id}", headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["name"] == "MV Test Carrier"

    res = client.put(f"/api/v1/ships/{ship_id}", json={"name": "MV Renamed"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["name"] == "MV Renamed"

    res = client.get("/api/v1/ships?page=1&per_page=10", headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["total"] >= 1

    res = client.get("/api/v1/ships/stats", headers=admin_headers)
    assert res.status_code == 200

    res = client.delete(f"/api/v1/ships/{ship_id}", headers=admin_headers)
    assert res.status_code == 200


def test_containers_crud(client, admin_headers):
    res = client.post("/api/v1/containers", json={
        "container_id": "CNT-TEST-1", "container_type": "20ft",
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()
    container_id = res.get_json()["data"]["id"]

    res = client.get(f"/api/v1/containers/{container_id}", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/containers/stats", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/containers/type-distribution", headers=admin_headers)
    assert res.status_code == 200

    res = client.delete(f"/api/v1/containers/{container_id}", headers=admin_headers)
    assert res.status_code == 200


def test_trucks_crud(client, admin_headers):
    res = client.post("/api/v1/trucks", json={
        "truck_number": "TRK-TEST-1", "truck_type": "Prime Mover",
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()
    truck_id = res.get_json()["data"]["id"]

    res = client.get(f"/api/v1/trucks/{truck_id}", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/trucks/stats", headers=admin_headers)
    assert res.status_code == 200

    res = client.delete(f"/api/v1/trucks/{truck_id}", headers=admin_headers)
    assert res.status_code == 200


def test_truck_operator_only_sees_own_trucks(client, db, admin_headers):
    """Regression test: a Truck Operator's fleet list must be scoped to
    their own trucks (matched by phone via driver_phone/owner_contact --
    the Truck model has no direct owner_user_id FK), not the whole port's
    fleet."""
    from tests.conftest import make_user, auth_headers
    from app.models import Truck, TruckType, UserRole

    mine = Truck(truck_number="TRK-MINE-1", truck_type=TruckType.TRAILER, driver_phone="+91-9000000001")
    other = Truck(truck_number="TRK-OTHER-1", truck_type=TruckType.TRAILER, driver_phone="+91-9000000002")
    db.session.add_all([mine, other])
    db.session.commit()

    operator = make_user(db, "operator@test.local", UserRole.TRUCK_OPERATOR)
    operator.phone = "+91-9000000001"
    db.session.commit()
    headers = auth_headers(client, "operator@test.local")

    res = client.get("/api/v1/trucks?per_page=100", headers=headers)
    assert res.status_code == 200
    numbers = [t["truck_number"] for t in res.get_json()["data"]["items"]]
    assert "TRK-MINE-1" in numbers
    assert "TRK-OTHER-1" not in numbers

    # Admin still sees the whole fleet.
    res = client.get("/api/v1/trucks?per_page=100", headers=admin_headers)
    numbers = [t["truck_number"] for t in res.get_json()["data"]["items"]]
    assert "TRK-MINE-1" in numbers and "TRK-OTHER-1" in numbers


def test_berths_crud_and_assignment(client, admin_headers):
    res = client.post("/api/v1/berths", json={
        "berth_id": "BTH-TEST-1", "name": "Test Berth", "code": "TB1",
        "max_length": 300,
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()
    berth_id = res.get_json()["data"]["id"]

    res = client.post("/api/v1/ships", json={
        "ship_id": "SH-TEST-2", "name": "MV Berth Test",
        "vessel_type": "Container Ship", "flag": "India", "length_overall": 200,
    }, headers=admin_headers)
    ship_id = res.get_json()["data"]["id"]

    res = client.post(f"/api/v1/berths/{berth_id}/assign", json={"ship_id": ship_id}, headers=admin_headers)
    assert res.status_code == 200, res.get_json()

    # Regression test: an occupied berth's serialization must surface which
    # ship is actually docked there, not just the bare current_ship_id.
    res = client.get(f"/api/v1/berths/{berth_id}", headers=admin_headers)
    assert res.status_code == 200
    berth_data = res.get_json()["data"]
    assert berth_data["current_ship"] is not None
    assert berth_data["current_ship"]["name"] == "MV Berth Test"

    res = client.get("/api/v1/berths?per_page=50", headers=admin_headers)
    listed = next(b for b in res.get_json()["data"]["items"] if b["id"] == berth_id)
    assert listed["current_ship"]["ship_id"] == "SH-TEST-2"

    res = client.get("/api/v1/berths/available", headers=admin_headers)
    assert res.status_code == 200

    res = client.post(f"/api/v1/berths/{berth_id}/release", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/berths/stats", headers=admin_headers)
    assert res.status_code == 200


def test_search_across_resources(client, admin_headers):
    client.post("/api/v1/ships", json={
        "ship_id": "SH-SEARCH", "name": "Searchable Vessel",
        "vessel_type": "Tanker", "flag": "Panama",
    }, headers=admin_headers)
    res = client.get("/api/v1/search?q=Searchable", headers=admin_headers)
    assert res.status_code == 200
