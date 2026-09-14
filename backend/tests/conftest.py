import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("FLASK_ENV", "testing")

import pytest
from app import create_app
from app.extensions import db as _db
from app.models import User, UserRole, UserStatus


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


def make_user(db, email, role, password="testpass123", status=UserStatus.ACTIVE):
    user = User(
        email=email, first_name="Test", last_name=role.name.title(),
        role=role, status=status,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def auth_headers(client, email, password="testpass123"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.get_json()
    token = res.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_user(db):
    return make_user(db, "admin@test.local", UserRole.SUPER_ADMIN)


@pytest.fixture()
def admin_headers(client, admin_user):
    return auth_headers(client, admin_user.email)


@pytest.fixture()
def staff_user(db):
    return make_user(db, "staff@test.local", UserRole.PORT_STAFF)


@pytest.fixture()
def staff_headers(client, staff_user):
    return auth_headers(client, staff_user.email)
