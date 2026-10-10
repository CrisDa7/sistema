"""Pruebas del módulo de autenticación administrativa."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from flask import session
from sqlalchemy import select
from werkzeug.security import check_password_hash

from app import create_app
from app.extensions import db
from app.models.admin import Admin, AdminSession
from app.models.client import Client
from app.services.admin_service import create_admin_account, get_current_admin, issue_session_for_admin
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig
from tests.test_helpers import generate_valid_cedula


def _unique_username(prefix: str) -> str:
    suffix = "".join(ch for ch in uuid.uuid4().hex if ch.isalpha())[:8]
    return f"{prefix}_{suffix}"


def _delete_exact_admin_ids(admin_ids):
    if not admin_ids:
        return
    ids = list(admin_ids)
    db.session.execute(db.delete(AdminSession).where(AdminSession.admin_id.in_(ids)))
    db.session.execute(db.delete(Admin).where(Admin.id.in_(ids)))
    db.session.commit()


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        ensure_test_database()
        db.session.execute(db.delete(AdminSession))
        db.session.execute(db.delete(Admin))
        db.session.commit()
        yield app

    with app.app_context():
        ensure_test_database()
        db.session.execute(db.delete(AdminSession))
        db.session.execute(db.delete(Admin))
        db.session.commit()


@pytest.fixture
def tracked_admin_ids(app):
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_admin_ids(created_ids)


def test_health_endpoint_is_public(app):
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_admin_login_success_and_hash(app, tracked_admin_ids):
    client = app.test_client()
    username = _unique_username("admin_ok")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)
        assert admin.password_hash != "StrongPass!123"
        assert check_password_hash(admin.password_hash, "StrongPass!123")

    csrf_response = client.get("/api/auth/csrf")
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200
    assert login_response.get_json()["admin"]["username"] == username
    assert client.get_cookie("session") is not None


def test_admin_login_rejects_invalid_credentials(app):
    client = app.test_client()
    username = _unique_username("admin_bad")

    with app.app_context():
        create_admin_account(username, "CorrectPass!123")

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "WrongPass!123", "csrf_token": csrf_token},
    )
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.get_json()["error"]


def test_admin_logout_revokes_session(app, tracked_admin_ids):
    client = app.test_client()
    username = _unique_username("admin_logout")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]
    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    with client.session_transaction() as sess:
        current_csrf = sess["csrf_token"]
        session_id = sess["session_id"]

    with app.app_context():
        session_row = db.session.get(AdminSession, session_id)
        assert session_row is not None

    logout_response = client.post(
        "/api/auth/logout",
        json={"csrf_token": current_csrf},
    )
    assert logout_response.status_code == 200

    with app.app_context():
        db_row = db.session.get(AdminSession, session_id)
        assert db_row is not None
        assert db_row.revoked_at is not None

    status_response = client.get("/api/auth/session")
    assert status_response.status_code == 200
    assert status_response.get_json()["authenticated"] is False


def test_admin_session_expiration(app, tracked_admin_ids):
    client = app.test_client()
    username = _unique_username("admin_expire")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]
    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    with client.session_transaction() as sess:
        session_id = sess["session_id"]

    with app.app_context():
        session_row = db.session.get(AdminSession, session_id)
        assert session_row is not None
        session_row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.session.commit()

    session_response = client.get("/api/auth/session")
    assert session_response.status_code == 401


def test_csrf_is_required_and_validates(app):
    client = app.test_client()
    username = _unique_username("admin_csrf")

    with app.app_context():
        create_admin_account(username, "StrongPass!123")

    csrf_response = client.get("/api/auth/csrf")
    token = csrf_response.get_json()["csrf_token"]

    invalid_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": "bad-token"},
    )
    assert invalid_response.status_code == 403

    valid_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": token},
    )
    assert valid_response.status_code == 200


def test_protected_endpoints_require_auth(app):
    client = app.test_client()
    response = client.get("/api/clients")
    assert response.status_code == 401


def test_bruteforce_protection_blocks_after_limit(app):
    client = app.test_client()
    username = _unique_username("admin_bruteforce")

    with app.app_context():
        create_admin_account(username, "StrongPass!123")

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    for _ in range(5):
        response = client.post(
            "/api/auth/login",
            json={"username": username, "password": "wrong-pass", "csrf_token": csrf_token},
        )
        assert response.status_code in {401, 429}

    blocked_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert blocked_response.status_code == 429


def test_single_admin_mvp_restricts_multiple_admins(app):
    with app.app_context():
        first = create_admin_account(_unique_username("admin_first"), "Password1!")
        with pytest.raises(Exception):
            create_admin_account(_unique_username("admin_second"), "Password2!")
        assert first.id is not None


def test_login_response_does_not_expose_session_id(app, tracked_admin_ids):
    """Verifica que POST /api/auth/login no expone session_id en JSON."""
    client = app.test_client()
    username = _unique_username("admin_no_exposure")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200
    response_data = login_response.get_json()
    assert "session_id" not in response_data
    assert response_data["admin"]["username"] == username


def test_session_status_does_not_expose_session_id(app, tracked_admin_ids):
    """Verifica que GET /api/auth/session no expone session_id ni csrf_token en JSON."""
    client = app.test_client()
    username = _unique_username("admin_session_no_exposure")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    session_response = client.get("/api/auth/session")
    assert session_response.status_code == 200
    response_data = session_response.get_json()
    assert "session_id" not in response_data
    assert "csrf_token" not in response_data
    assert response_data["authenticated"] is True


def test_csrf_token_works_for_protected_operation(app, tracked_admin_ids):
    """Verifica que el cliente puede obtener CSRF y usarlo en operación protegida."""
    client = app.test_client()
    username = _unique_username("admin_csrf_op")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    # Obtener nuevo CSRF después del login
    new_csrf_response = client.get("/api/auth/csrf")
    new_csrf_token = new_csrf_response.get_json()["csrf_token"]

    # Usar CSRF en operación protegida (logout)
    logout_response = client.post(
        "/api/auth/logout",
        json={"csrf_token": new_csrf_token},
    )
    assert logout_response.status_code == 200


def test_logout_revokes_session_and_session_status_returns_false(app, tracked_admin_ids):
    """Verifica que logout revoca la sesión y /api/auth/session devuelve authenticated=false."""
    client = app.test_client()
    username = _unique_username("admin_logout_verify")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    # Verificar sesión activa antes de logout
    session_before = client.get("/api/auth/session")
    assert session_before.status_code == 200
    assert session_before.get_json()["authenticated"] is True

    # Logout
    with client.session_transaction() as sess:
        current_csrf = sess["csrf_token"]

    logout_response = client.post(
        "/api/auth/logout",
        json={"csrf_token": current_csrf},
    )
    assert logout_response.status_code == 200

    # Verificar sesión inactiva después de logout
    session_after = client.get("/api/auth/session")
    assert session_after.status_code == 200
    assert session_after.get_json()["authenticated"] is False


def test_business_routes_require_csrf(app, tracked_admin_ids):
    """Verifica que las rutas de negocio requieren token CSRF."""
    client = app.test_client()
    username = _unique_username("admin_csrf_business")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200
    new_csrf_response = client.get("/api/auth/csrf")
    assert new_csrf_response.status_code == 200
    csrf_token = new_csrf_response.get_json()["csrf_token"]

    # Usar cédulas conocidas válidas de test_client_validation.py
    cedula_bad_token = "0102030400"
    cedula_valid = "1710034065"

    response_missing = client.post(
        "/api/clients",
        json={"first_name": "Test"},
    )
    assert response_missing.status_code == 403

    # Intentar POST con token inválido debe fallar
    response_bad_token = client.post("/api/clients", json={"cedula": cedula_bad_token, "first_name": "Test", "Last Name": "User", "phone": "0998765432", "csrf_token": "invalid-token"})
    assert response_bad_token.status_code == 403

    # POST con token válido debe funcionar
    response_valid = client.post(
        "/api/clients",
        json={
            "cedula": cedula_valid,
            "first_name": "Test",
            "last_name": "User",
            "phone": "0998765432",
            "csrf_token": csrf_token,
        },
    )

    assert response_valid.status_code == 201

    # Limpiar clientes creados por esta prueba
    with app.app_context():
        ensure_test_database()
        db.session.execute(db.delete(Client).where(Client.cedula.in_([cedula_bad_token, cedula_valid])))
        db.session.commit()


def test_get_routes_do_not_require_csrf(app, tracked_admin_ids):
    """Verifica que las rutas GET no requieren CSRF."""
    client = app.test_client()
    username = _unique_username("admin_get_csrf")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    # GET sin token debe funcionar
    response = client.get("/api/clients")
    assert response.status_code == 200


def test_logout_requires_csrf_token(app, tracked_admin_ids):
    """Verifica que logout requiera token CSRF válido."""
    client = app.test_client()
    username = _unique_username("admin_logout_csrf")

    with app.app_context():
        admin = create_admin_account(username, "StrongPass!123")
        tracked_admin_ids.add(admin.id)

    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    # Logout sin token debe fallar
    logout_no_token = client.post("/api/auth/logout", json={})
    assert logout_no_token.status_code == 403

    # Logout con token inválido debe fallar
    logout_bad_token = client.post("/api/auth/logout", json={"csrf_token": "invalid-token"})
    assert logout_bad_token.status_code == 403

    # Logout con token válido debe funcionar
    with client.session_transaction() as sess:
        current_csrf = sess["csrf_token"]

    logout_valid = client.post("/api/auth/logout", json={"csrf_token": current_csrf})
    assert logout_valid.status_code == 200


def test_unauthenticated_request_returns_401_before_csrf_check(app):
    """Verifica que autenticación falla antes de validar CSRF."""
    client = app.test_client()

    # POST sin autenticación debe retornar 401, no 403
    response = client.post("/api/clients", json={"cedula": "0102030400", "first_name": "Test", "last_name": "User", "phone": "0998765432"})
    assert response.status_code == 401
    assert "Autenticación requerida" in response.get_json()["error"]
