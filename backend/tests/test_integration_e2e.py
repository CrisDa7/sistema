"""Pruebas de integración end-to-end del backend de Active Gym.

Estas pruebas verifican el flujo completo mediante el cliente HTTP de Flask:
autenticación, registro de clientes, creación de áreas/planes, membresías,
pagos, renovaciones y validación de reglas de negocio.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app import create_app
from app.extensions import db
from app.models.admin import Admin, AdminSession
from app.models.area import Area
from app.models.client import Client
from app.models.membership import Membership, membership_areas
from app.models.payment import Payment
from app.models.plan import Plan, plan_areas
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig
from tests.test_helpers import generate_valid_cedula


def _cleanup_e2e_data(
    client_ids=None,
    area_ids=None,
    plan_ids=None,
    membership_ids=None,
    payment_ids=None,
    admin_username=None,
):
    """Limpia exactamente los datos creados por pruebas E2E."""
    if payment_ids:
        db.session.execute(db.delete(Payment).where(Payment.id.in_(payment_ids)))
    if membership_ids:
        db.session.execute(
            db.delete(membership_areas).where(membership_areas.c.membership_id.in_(membership_ids))
        )
        db.session.execute(db.delete(Membership).where(Membership.id.in_(membership_ids)))
    if plan_ids:
        db.session.execute(db.delete(plan_areas).where(plan_areas.c.plan_id.in_(plan_ids)))
        db.session.execute(db.delete(Plan).where(Plan.id.in_(plan_ids)))
    if area_ids:
        db.session.execute(db.delete(Area).where(Area.id.in_(area_ids)))
    if client_ids:
        db.session.execute(db.delete(Client).where(Client.id.in_(client_ids)))
    if admin_username:
        admin = db.session.execute(select(Admin).where(Admin.username == admin_username)).scalar_one_or_none()
        if admin:
            db.session.execute(db.delete(AdminSession).where(AdminSession.admin_id == admin.id))
            db.session.execute(db.delete(Admin).where(Admin.id == admin.id))
    db.session.commit()


@pytest.fixture
def app():
    """Aplicación configurada para pruebas E2E."""
    app = create_app(TestConfig)
    with app.app_context():
        ensure_test_database()
        yield app


@pytest.fixture
def authenticated_client(app):
    """Cliente autenticado con CSRF para pruebas E2E."""
    from app.services.admin_service import create_admin_account

    with app.app_context():
        ensure_test_database()
        # Limpiar admin e2e si existe de pruebas anteriores
        existing_admin = db.session.execute(select(Admin).where(Admin.username == "admin_e2e")).scalar_one_or_none()
        if existing_admin:
            db.session.execute(db.delete(AdminSession).where(AdminSession.admin_id == existing_admin.id))
            db.session.execute(db.delete(Admin).where(Admin.id == existing_admin.id))
            db.session.commit()
        admin = create_admin_account("admin_e2e", "StrongPass!123")

    client = app.test_client()
    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin_e2e", "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    csrf_response = client.get("/api/auth/csrf")
    current_csrf = csrf_response.get_json()["csrf_token"]

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


def test_e2e_complete_membership_flow(app, authenticated_client):
    """Flujo completo: autenticación → cliente → áreas → plan → membresía → pago → renovación."""
    client = authenticated_client

    # Paso 1: Registrar cliente con cédula válida
    cedula = generate_valid_cedula(100000)
    client_response = client.post(
        "/api/clients",
        json={
            "cedula": cedula,
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone": "0991234567",
        },
    )
    assert client_response.status_code == 201
    client_data = client_response.get_json()
    client_id = client_data["id"]
    assert client_data["cedula"] == cedula

    # Paso 2: Crear áreas de entrenamiento
    area1_response = client.post("/api/areas", json={"name": "Pesas"})
    assert area1_response.status_code == 201
    area1_id = area1_response.get_json()["id"]

    area2_response = client.post("/api/areas", json={"name": "Cardio"})
    assert area2_response.status_code == 201
    area2_id = area2_response.get_json()["id"]

    # Paso 3: Crear plan asociado a áreas
    plan_response = client.post(
        "/api/plans",
        json={"name": "Mensual Completo", "price": "50.00", "area_ids": [area1_id, area2_id]},
    )
    assert plan_response.status_code == 201
    plan_data = plan_response.get_json()
    plan_id = plan_data["id"]
    assert len(plan_data["areas"]) == 2

    # Paso 4: Registrar membresía
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    membership_response = client.post(
        "/api/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "area_ids": [area1_id, area2_id],
            "contracted_price": "50.00",
        },
    )
    assert membership_response.status_code == 201
    membership_data = membership_response.get_json()
    membership_id = membership_data["id"]
    assert membership_data["client_id"] == client_id
    assert membership_data["plan_id"] == plan_id
    assert len(membership_data["areas"]) == 2
    assert membership_data["status"] == "vigente"

    # Paso 5: Registrar pago completo
    payment_response = client.post(
        f"/api/memberships/{membership_id}/payments",
        json={
            "amount": "50.00",
            "payment_method": "cash",
            "payment_date": date.today().isoformat(),
        },
    )
    assert payment_response.status_code == 201
    payment_data = payment_response.get_json()
    payment_id = payment_data["id"]
    assert payment_data["amount"] == "50.00"

    # Paso 6: Verificar estado de pago
    status_response = client.get(f"/api/memberships/{membership_id}/payment-status")
    assert status_response.status_code == 200
    status_data = status_response.get_json()
    assert status_data["paid"] is True
    assert status_data["payment_id"] == payment_id

    # Paso 7: Renovar membresía por continuidad
    renew_response = client.post(
        f"/api/memberships/{membership_id}/renew",
        json={"mode": "continuity", "area_ids": [area1_id, area2_id], "contracted_price": "50.00"},
    )
    assert renew_response.status_code == 201
    renew_data = renew_response.get_json()
    new_membership_id = renew_data["id"]
    assert renew_data["client_id"] == client_id
    assert renew_data["plan_id"] == plan_id

    # Verificar que la nueva membresía inicia el día siguiente
    with app.app_context():
        new_membership = db.session.get(Membership, new_membership_id)
        assert new_membership.start_date == end_date + timedelta(days=1)

    # Limpieza
    with app.app_context():
        ensure_test_database()
        _cleanup_e2e_data(
            client_ids=[client_id],
            area_ids=[area1_id, area2_id],
            plan_ids=[plan_id],
            membership_ids=[membership_id, new_membership_id],
            payment_ids=[payment_id],
            admin_username="admin_e2e",
        )


def test_e2e_membership_conflict_same_areas(app, authenticated_client):
    """Verifica que membresías con mismas áreas y fechas solapadas sean rechazadas."""
    client = authenticated_client

    # Crear cliente
    cedula = generate_valid_cedula(100001)
    client_response = client.post(
        "/api/clients",
        json={"cedula": cedula, "first_name": "María", "last_name": "García", "phone": "0998765432"},
    )
    client_id = client_response.get_json()["id"]

    # Crear área
    area_response = client.post("/api/areas", json={"name": "Yoga"})
    area_id = area_response.get_json()["id"]

    # Crear plan
    plan_response = client.post(
        "/api/plans",
        json={"name": "Yoga Mensual", "price": "30.00", "area_ids": [area_id]},
    )
    plan_id = plan_response.get_json()["id"]

    # Primera membresía
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    membership1_response = client.post(
        "/api/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "area_ids": [area_id],
            "contracted_price": "30.00",
        },
    )
    assert membership1_response.status_code == 201
    membership1_id = membership1_response.get_json()["id"]

    # Segunda membresía con mismas áreas y fechas solapadas (debe fallar)
    overlapping_start = start_date + timedelta(days=15)
    overlapping_end = overlapping_start + timedelta(days=30)
    membership2_response = client.post(
        "/api/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": overlapping_start.isoformat(),
            "end_date": overlapping_end.isoformat(),
            "area_ids": [area_id],
            "contracted_price": "30.00",
        },
    )
    assert membership2_response.status_code == 409
    assert "conflicto" in membership2_response.get_json()["error"].lower()

    # Limpieza
    with app.app_context():
        ensure_test_database()
        _cleanup_e2e_data(
            client_ids=[client_id],
            area_ids=[area_id],
            plan_ids=[plan_id],
            membership_ids=[membership1_id],
            admin_username="admin_e2e",
        )


def test_e2e_simultaneous_memberships_different_areas(app, authenticated_client):
    """Verifica que membresías simultáneas con áreas diferentes sean permitidas."""
    client = authenticated_client

    # Crear cliente
    cedula = generate_valid_cedula(100002)
    client_response = client.post(
        "/api/clients",
        json={"cedula": cedula, "first_name": "Carlos", "last_name": "López", "phone": "0995555555"},
    )
    client_id = client_response.get_json()["id"]

    # Crear áreas diferentes
    area1_response = client.post("/api/areas", json={"name": "Piscina"})
    area1_id = area1_response.get_json()["id"]

    area2_response = client.post("/api/areas", json={"name": "Spinning"})
    area2_id = area2_response.get_json()["id"]

    # Crear planes para cada área
    plan1_response = client.post(
        "/api/plans",
        json={"name": "Piscina Mensual", "price": "40.00", "area_ids": [area1_id]},
    )
    plan1_id = plan1_response.get_json()["id"]

    plan2_response = client.post(
        "/api/plans",
        json={"name": "Spinning Mensual", "price": "35.00", "area_ids": [area2_id]},
    )
    plan2_id = plan2_response.get_json()["id"]

    # Primera membresía (Piscina)
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    membership1_response = client.post(
        "/api/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan1_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "area_ids": [area1_id],
            "contracted_price": "40.00",
        },
    )
    assert membership1_response.status_code == 201
    membership1_id = membership1_response.get_json()["id"]

    # Segunda membresía (Spinning) con fechas solapadas pero áreas diferentes (debe funcionar)
    membership2_response = client.post(
        "/api/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan2_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "area_ids": [area2_id],
            "contracted_price": "35.00",
        },
    )
    assert membership2_response.status_code == 201
    membership2_id = membership2_response.get_json()["id"]

    # Limpieza
    with app.app_context():
        ensure_test_database()
        _cleanup_e2e_data(
            client_ids=[client_id],
            area_ids=[area1_id, area2_id],
            plan_ids=[plan1_id, plan2_id],
            membership_ids=[membership1_id, membership2_id],
            admin_username="admin_e2e",
        )


def test_e2e_duplicate_payment_rejected(app, authenticated_client):
    """Verifica que pagos duplicados para la misma membresía sean rechazados."""
    client = authenticated_client

    # Crear cliente, área, plan, membresía
    cedula = generate_valid_cedula(100003)
    client_response = client.post(
        "/api/clients",
        json={"cedula": cedula, "first_name": "Ana", "last_name": "Martínez", "phone": "0993333333"},
    )
    client_id = client_response.get_json()["id"]

    area_response = client.post("/api/areas", json={"name": "Crossfit"})
    area_id = area_response.get_json()["id"]

    plan_response = client.post(
        "/api/plans",
        json={"name": "Crossfit Mensual", "price": "60.00", "area_ids": [area_id]},
    )
    plan_id = plan_response.get_json()["id"]

    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    membership_response = client.post(
        "/api/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "area_ids": [area_id],
            "contracted_price": "60.00",
        },
    )
    membership_id = membership_response.get_json()["id"]

    # Primer pago
    payment1_response = client.post(
        f"/api/memberships/{membership_id}/payments",
        json={
            "amount": "60.00",
            "payment_method": "cash",
            "payment_date": date.today().isoformat(),
        },
    )
    assert payment1_response.status_code == 201

    # Segundo pago (debe fallar)
    payment2_response = client.post(
        f"/api/memberships/{membership_id}/payments",
        json={
            "amount": "60.00",
            "payment_method": "cash",
            "payment_date": date.today().isoformat(),
        },
    )
    assert payment2_response.status_code == 409
    assert "pago" in payment2_response.get_json()["error"].lower()

    # Limpieza
    with app.app_context():
        ensure_test_database()
        payment1_id = payment1_response.get_json()["id"]
        _cleanup_e2e_data(
            client_ids=[client_id],
            area_ids=[area_id],
            plan_ids=[plan_id],
            membership_ids=[membership_id],
            payment_ids=[payment1_id],
            admin_username="admin_e2e",
        )


def test_e2e_payment_amount_must_match_contracted_price(app, authenticated_client):
    """Verifica que el monto del pago coincida exactamente con el precio contratado."""
    client = authenticated_client

    # Crear cliente, área, plan, membresía
    cedula = generate_valid_cedula(100004)
    client_response = client.post(
        "/api/clients",
        json={"cedula": cedula, "first_name": "Pedro", "last_name": "Sánchez", "phone": "0992222222"},
    )
    client_id = client_response.get_json()["id"]

    area_response = client.post("/api/areas", json={"name": "Box"})
    area_id = area_response.get_json()["id"]

    plan_response = client.post(
        "/api/plans",
        json={"name": "Box Mensual", "price": "45.00", "area_ids": [area_id]},
    )
    plan_id = plan_response.get_json()["id"]

    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    membership_response = client.post(
        "/api/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "area_ids": [area_id],
            "contracted_price": "45.00",
        },
    )
    membership_id = membership_response.get_json()["id"]

    # Pago con monto incorrecto (debe fallar)
    payment_response = client.post(
        f"/api/memberships/{membership_id}/payments",
        json={
            "amount": "40.00",
            "payment_method": "cash",
            "payment_date": date.today().isoformat(),
        },
    )
    assert payment_response.status_code == 400
    assert "coincidir" in payment_response.get_json()["error"].lower()

    # Limpieza
    with app.app_context():
        ensure_test_database()
        _cleanup_e2e_data(
            client_ids=[client_id],
            area_ids=[area_id],
            plan_ids=[plan_id],
            membership_ids=[membership_id],
            admin_username="admin_e2e",
        )


def test_e2e_duplicate_cedula_rejected(app, authenticated_client):
    """Verifica que cédulas duplicadas sean rechazadas."""
    client = authenticated_client

    cedula = generate_valid_cedula(100005)

    # Primer cliente
    client1_response = client.post(
        "/api/clients",
        json={"cedula": cedula, "first_name": "Laura", "last_name": "Díaz", "phone": "0991111111"},
    )
    assert client1_response.status_code == 201
    client1_id = client1_response.get_json()["id"]

    # Segundo cliente con misma cédula (debe fallar)
    client2_response = client.post(
        "/api/clients",
        json={"cedula": cedula, "first_name": "Sofía", "last_name": "Ruiz", "phone": "0990000000"},
    )
    assert client2_response.status_code == 409
    assert "cédula" in client2_response.get_json()["error"].lower()

    # Limpieza
    with app.app_context():
        ensure_test_database()
        _cleanup_e2e_data(client_ids=[client1_id], admin_username="admin_e2e")


def test_e2e_unauthenticated_request_rejected(app):
    """Verifica que solicitudes sin autenticación sean rechazadas."""
    client = app.test_client()

    response = client.post("/api/clients", json={"cedula": "0102030400", "first_name": "Test", "last_name": "User", "phone": "0991234567"})
    assert response.status_code == 401

    # Limpieza: asegurar que no quede admin residual
    with app.app_context():
        ensure_test_database()
        _cleanup_e2e_data(admin_username="admin_e2e")


def test_e2e_request_without_csrf_rejected(app, authenticated_client):
    """Verifica que solicitudes de escritura sin CSRF sean rechazadas."""
    client = app.test_client()

    # Autenticar primero para tener sesión válida
    csrf_response = client.get("/api/auth/csrf")
    csrf_token = csrf_response.get_json()["csrf_token"]

    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin_e2e", "password": "StrongPass!123", "csrf_token": csrf_token},
    )
    assert login_response.status_code == 200

    # Intentar POST sin CSRF (no enviar ni en encabezado ni en JSON)
    response = client.post("/api/areas", json={"name": "Test No CSRF"})
    assert response.status_code == 403

    # Limpieza
    with app.app_context():
        ensure_test_database()
        _cleanup_e2e_data(admin_username="admin_e2e")
