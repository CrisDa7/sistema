"""Configuración global de pytest para Active Gym.

No se define autouse ni fixtures automáticas para no interferir con las pruebas
existentes del dominio ni con la autenticación explícita del módulo auth.
"""

import uuid

import pytest

from app import create_app
from app.extensions import db
from app.models.admin import Admin, AdminSession
from app.services.admin_service import create_admin_account
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig


@pytest.fixture
def app():
    """Crea la aplicación con base de pruebas segura y limpia de autenticación."""
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
def authenticated_admin(app):
    """Crea un administrador temporal y lo elimina con limpieza exacta al finalizar."""
    with app.app_context():
        ensure_test_database()
        db.session.execute(db.delete(AdminSession))
        db.session.execute(db.delete(Admin))
        db.session.commit()

        username = f"admin_test_{uuid.uuid4().hex[:8]}"
        admin = create_admin_account(username, "StrongPass!123")
        yield admin

        db.session.execute(db.delete(AdminSession).where(AdminSession.admin_id == admin.id))
        db.session.execute(db.delete(Admin).where(Admin.id == admin.id))
        db.session.commit()


@pytest.fixture
def authenticated_client(app, authenticated_admin):
    """Devuelve un cliente de prueba con sesión administrativa válida y CSRF activo."""
    client = app.test_client()
    csrf_response = client.get("/api/auth/csrf")
    assert csrf_response.status_code == 200
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": authenticated_admin.username,
            "password": "StrongPass!123",
            "csrf_token": csrf_token,
        },
    )
    assert login_response.status_code == 200

    # Obtener el token vigente después del login.
    csrf_response = client.get("/api/auth/csrf")
    assert csrf_response.status_code == 200
    current_csrf = csrf_response.get_json()["csrf_token"]

    # Adjuntar el token como encabezado, sin modificar el JSON.
    original_open = client.open

    def open_with_csrf(*args, **kwargs):
        method = kwargs.get("method", "GET").upper()

        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("X-CSRF-Token", current_csrf)
            kwargs["headers"] = headers

        return original_open(*args, **kwargs)

    client.open = open_with_csrf

    return client