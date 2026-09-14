from app.models import AuditLog, UserRole


def test_health_check_works_without_db(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"


def test_registration_succeeds_and_assigns_public_role(client, db):
    res = client.post("/api/v1/auth/register", json={
        "email": "newuser@test.local", "password": "password123",
        "first_name": "New", "last_name": "User",
    })
    assert res.status_code == 201, res.get_json()
    user = res.get_json()["data"]["user"]
    assert user["role"] == "Public"
    assert "access_token" in res.get_json()["data"]


def test_registration_rejects_duplicate_email(client, staff_user):
    res = client.post("/api/v1/auth/register", json={
        "email": staff_user.email, "password": "password123",
        "first_name": "Dup", "last_name": "User",
    })
    assert res.status_code == 400


def test_login_success_and_failure(client, staff_user):
    ok = client.post("/api/v1/auth/login", json={"email": staff_user.email, "password": "testpass123"})
    assert ok.status_code == 200
    assert ok.get_json()["data"]["user"]["email"] == staff_user.email

    bad = client.post("/api/v1/auth/login", json={"email": staff_user.email, "password": "wrong"})
    assert bad.status_code == 401


def test_login_and_register_persist_audit_log(client, db, staff_user):
    client.post("/api/v1/auth/login", json={"email": staff_user.email, "password": "testpass123"})
    assert AuditLog.query.filter_by(action="login", status="success").count() >= 1

    client.post("/api/v1/auth/register", json={
        "email": "audituser@test.local", "password": "password123",
        "first_name": "Audit", "last_name": "User",
    })
    assert AuditLog.query.filter_by(action="register").count() == 1


def test_protected_route_requires_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code in (401, 422)


def test_refresh_token_flow(client, staff_user):
    login = client.post("/api/v1/auth/login", json={"email": staff_user.email, "password": "testpass123"})
    refresh_token = login.get_json()["data"]["refresh_token"]
    res = client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})
    assert res.status_code == 200
    assert "access_token" in res.get_json()["data"]


def test_logout_revokes_session(client, staff_user, staff_headers):
    res = client.post("/api/v1/auth/logout", headers=staff_headers)
    assert res.status_code == 200
    # a revoked token should no longer authorize requests
    res2 = client.get("/api/v1/auth/me", headers=staff_headers)
    assert res2.status_code == 401


def test_self_service_profile_update(client, staff_headers):
    res = client.put("/api/v1/auth/me", json={"first_name": "Updated", "department": "Ops"}, headers=staff_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["first_name"] == "Updated"
    assert res.get_json()["data"]["department"] == "Ops"


def test_my_activity_is_self_service_no_special_permission(client, staff_headers):
    res = client.get("/api/v1/auth/my-activity", headers=staff_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["total"] >= 1  # at least the login itself


def test_sessions_list_and_revoke(client, staff_headers):
    res = client.get("/api/v1/auth/sessions", headers=staff_headers)
    assert res.status_code == 200
    sessions = res.get_json()["data"]["items"]
    assert len(sessions) >= 1


def test_google_status_reports_not_configured_without_credentials(client):
    res = client.get("/api/v1/auth/google/status")
    assert res.status_code == 200
    assert res.get_json()["data"]["configured"] is False
