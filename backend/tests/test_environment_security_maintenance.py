from datetime import datetime, timedelta


def test_environment_readings_endpoints(client, admin_headers):
    for path in ["/api/v1/environment/air-quality", "/api/v1/environment/water-quality",
                 "/api/v1/environment/noise", "/api/v1/environment/weather",
                 "/api/v1/environment/emissions", "/api/v1/environment/alerts"]:
        res = client.get(path, headers=admin_headers)
        assert res.status_code == 200, f"{path} -> {res.status_code}: {res.get_json()}"


def test_environment_noise_by_station_and_emissions_by_source(client, admin_headers):
    res = client.get("/api/v1/environment/noise/by-station", headers=admin_headers)
    assert res.status_code == 200
    res = client.get("/api/v1/environment/emissions/by-source", headers=admin_headers)
    assert res.status_code == 200


def test_aqi_forecast_gracefully_unavailable_without_trained_model_or_data(client, admin_headers):
    # In the test DB there's no trained model file and no air quality history,
    # so this must degrade to an explicit "not available" response, never a
    # crash or a fabricated number.
    res = client.get("/api/v1/environment/air-quality/forecast", headers=admin_headers)
    assert res.status_code == 200
    body = res.get_json()["data"]
    assert body["available"] is False
    assert "message" in body


def test_security_incidents_and_alerts(client, admin_headers):
    res = client.post("/api/v1/security", json={
        "incident_id": "INC-TEST-1", "incident_type": "Intrusion",
        "zone": "Zone A - Berth 1-3", "severity": "Low", "title": "Test incident",
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()

    res = client.get("/api/v1/security?page=1&per_page=10", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/security/alerts", headers=admin_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/security/cameras", headers=admin_headers)
    assert res.status_code == 200


def test_security_access_logs_reflects_real_audit_trail(client, admin_headers, admin_user):
    res = client.get("/api/v1/security/access-logs", headers=admin_headers)
    assert res.status_code == 200
    items = res.get_json()["data"]["items"]
    assert len(items) >= 1
    assert items[0]["action"] == "login"
    assert items[0]["user_email"] == admin_user.email


def test_maintenance_equipment_and_schedule(client, admin_headers):
    res = client.post("/api/v1/maintenance", json={
        "equipment_id": "EQ-TEST-1", "name": "Test Crane", "equipment_type": "Ship-to-Shore Crane",
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()
    equipment_id = res.get_json()["data"]["id"]

    res = client.post("/api/v1/maintenance/schedules", json={
        "equipment_id": equipment_id, "maintenance_type": "Preventive",
        "title": "Routine check", "scheduled_date": datetime.utcnow().isoformat(),
    }, headers=admin_headers)
    assert res.status_code == 201, res.get_json()

    res = client.get("/api/v1/maintenance/schedules", headers=admin_headers)
    assert res.status_code == 200


def test_maintenance_cost_by_month_is_real_not_fabricated(client, admin_headers, db):
    from app.models import Equipment, EquipmentType, EquipmentStatus, MaintenanceSchedule, MaintenanceType, MaintenanceStatus, MaintenancePriority

    eq = Equipment(equipment_id="EQ-COST-1", name="Cost Crane", equipment_type=EquipmentType.CRANE_STS, status=EquipmentStatus.OPERATIONAL)
    db.session.add(eq)
    db.session.commit()
    sched = MaintenanceSchedule(
        equipment_id=eq.id, maintenance_type=MaintenanceType.PREVENTIVE, priority=MaintenancePriority.MEDIUM,
        status=MaintenanceStatus.COMPLETED, title="Cost test", scheduled_date=datetime.utcnow(), actual_cost=12345,
    )
    db.session.add(sched)
    db.session.commit()

    res = client.get("/api/v1/maintenance/cost-by-month?months=1", headers=admin_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]["datasets"][0]["data"]
    assert data[-1] == 12345.0


def test_dashboard_kpis_and_charts(client, admin_headers):
    res = client.get("/api/v1/dashboard/kpis", headers=admin_headers)
    assert res.status_code == 200
    kpis = res.get_json()["data"]
    assert "total_ships" in kpis and "revenue" in kpis and "aqi" in kpis

    for path in [
        "/api/v1/dashboard/charts/throughput",
        "/api/v1/dashboard/charts/vessel-arrivals",
        "/api/v1/dashboard/charts/container-distribution",
        "/api/v1/dashboard/charts/truck-traffic",
        "/api/v1/dashboard/charts/equipment-health",
        "/api/v1/dashboard/charts/environmental-trends",
        "/api/v1/dashboard/vessel-status",
        "/api/v1/dashboard/berth-occupancy",
        "/api/v1/dashboard/recent-activity",
    ]:
        res = client.get(path, headers=admin_headers)
        assert res.status_code == 200, f"{path} -> {res.status_code}"


def test_berth_occupancy_uses_real_berth_table(client, admin_headers, db):
    from app.models import Berth, BerthStatus, Ship, ShipStatus, VesselType

    berth = Berth(berth_id="BTH-OCC-1", name="Occ Berth", code="OB1", max_length=300)
    ship = Ship(ship_id="SH-OCC-1", name="Occ Ship", vessel_type=VesselType.CONTAINER_SHIP,
                flag="India", status=ShipStatus.AT_BERTH, length_overall=150)
    db.session.add_all([berth, ship])
    db.session.commit()
    berth.current_ship_id = ship.id
    db.session.commit()

    res = client.get("/api/v1/dashboard/berth-occupancy", headers=admin_headers)
    assert res.status_code == 200
    occ = next(o for o in res.get_json()["data"] if o["berth_id"] == "BTH-OCC-1")
    assert occ["occupied"] is True
    assert occ["occupancy_pct"] == 50.0
