"""
Covers the RBAC consolidation: User.has_permission() must prefer a real
Role/Permission/RolePermission row over the hardcoded ROLE_PERMISSIONS
fallback once one exists, and the /api/v1/roles API must have a real,
verifiable effect on authorization (it was previously fully decorative).
"""
from app.models import User, UserRole, Role, Permission


def _fresh(db, user):
    # Read the id BEFORE expunging: after an intervening commit expires the
    # (still-attached) instance's attributes, expunging it first would leave
    # even `.id` unreadable (DetachedInstanceError on the implicit reload).
    user_id = user.id
    db.session.expunge(user)
    return User.query.get(user_id)


def test_permission_check_falls_back_to_hardcoded_dict_without_a_db_role(staff_user):
    # No Role row exists for "Port Staff" in a fresh test DB -> fallback dict
    # applies, which does grant ships.write to Port Staff.
    assert staff_user.has_permission("ships.write") is True


def test_db_role_row_overrides_the_hardcoded_dict(db, staff_user):
    read_perm = Permission(name="ships.read", module="ships", action="read")
    db.session.add(read_perm)
    db.session.commit()

    role_row = Role(name="port_staff", display_name="Port Staff", is_system=True)
    role_row.permissions.append(read_perm)
    db.session.add(role_row)
    db.session.commit()

    fresh_staff = _fresh(db, staff_user)
    assert fresh_staff.has_permission("ships.read") is True
    assert fresh_staff.has_permission("ships.write") is False


def test_editing_role_permissions_via_api_has_real_effect(client, db, admin_headers, staff_user):
    read_perm = Permission(name="ships.read", module="ships", action="read")
    write_perm = Permission(name="ships.write", module="ships", action="write")
    db.session.add_all([read_perm, write_perm])
    db.session.commit()

    role_row = Role(name="port_staff", display_name="Port Staff", is_system=True)
    role_row.permissions.append(read_perm)
    db.session.add(role_row)
    db.session.commit()

    fresh_staff = _fresh(db, staff_user)
    assert fresh_staff.has_permission("ships.write") is False

    res = client.put(f"/api/v1/roles/{role_row.id}",
                      json={"permission_ids": [read_perm.id, write_perm.id]}, headers=admin_headers)
    assert res.status_code == 200, res.get_json()

    fresh_staff2 = _fresh(db, fresh_staff)
    assert fresh_staff2.has_permission("ships.write") is True


def test_system_role_permissions_can_be_edited_but_not_renamed(client, db, admin_headers):
    perm = Permission(name="dashboard.read", module="dashboard", action="read")
    db.session.add(perm)
    db.session.commit()
    role_row = Role(name="port_staff", display_name="Port Staff", is_system=True)
    db.session.add(role_row)
    db.session.commit()

    # Permission edits on a system role must be allowed (this is the whole
    # point of making the Roles API real).
    res = client.put(f"/api/v1/roles/{role_row.id}", json={"permission_ids": [perm.id]}, headers=admin_headers)
    assert res.status_code == 200

    # But renaming a system role must be rejected -- display_name is matched
    # against UserRole.value to resolve permissions, so renaming it would
    # silently strand every user of that role.
    res = client.put(f"/api/v1/roles/{role_row.id}", json={"display_name": "Renamed"}, headers=admin_headers)
    assert res.status_code == 400


def test_role_delete_guard_blocks_deletion_of_an_in_use_role(client, db, admin_headers):
    role_row = Role(name="port_staff", display_name="Port Staff", is_system=False)
    db.session.add(role_row)
    db.session.commit()

    user = User(email="inuse@test.local", first_name="In", last_name="Use", role=UserRole.PORT_STAFF)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    res = client.delete(f"/api/v1/roles/{role_row.id}", headers=admin_headers)
    assert res.status_code == 400, res.get_json()


def test_role_delete_guard_allows_deletion_of_an_unused_role(client, db, admin_headers):
    role_row = Role(name="customer", display_name="Customer", is_system=False)
    db.session.add(role_row)
    db.session.commit()

    res = client.delete(f"/api/v1/roles/{role_row.id}", headers=admin_headers)
    assert res.status_code == 200, res.get_json()


def test_low_privilege_role_cannot_write_restricted_resources(client, db):
    public_user = User(email="public@test.local", first_name="Pub", last_name="Lic", role=UserRole.PUBLIC)
    public_user.set_password("password123")
    db.session.add(public_user)
    db.session.commit()

    res = client.post("/api/v1/auth/login", json={"email": "public@test.local", "password": "password123"})
    headers = {"Authorization": f"Bearer {res.get_json()['data']['access_token']}"}

    res = client.post("/api/v1/ships", json={
        "ship_id": "SH-DENY", "name": "Should Fail", "vessel_type": "Tanker", "flag": "India",
    }, headers=headers)
    assert res.status_code == 403
