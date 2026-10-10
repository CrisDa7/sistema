"""Pruebas adicionales para casos pendientes del Bloque 4."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models.area import Area
from app.models.client import Client
from app.models.membership import Membership, membership_areas
from app.models.payment import Payment
from app.models.plan import Plan, plan_areas
from app.services.membership_service import register_membership, renew_membership_continuity
from app.services.payment_service import register_payment
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig
from tests.test_helpers import generate_valid_cedula


def _cleanup_test_data(
    client_ids=None,
    area_ids=None,
    plan_ids=None,
    membership_ids=None,
    payment_ids=None,
):
    """Limpia datos creados por pruebas."""
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
    db.session.commit()


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        ensure_test_database()
        yield app


def test_membership_historical_snapshot_of_areas_and_price(app):
    """Verifica que las membresías guarden snapshot histórico de áreas y precio."""
    with app.app_context():
        ensure_test_database()

        # Crear cliente
        cedula = generate_valid_cedula(20000)
        client = Client(
            cedula=cedula,
            first_name="Test",
            last_name="User",
            phone="0991234567"
        )
        db.session.add(client)
        db.session.commit()

        # Crear áreas
        area1 = Area(name="Area Test 1")
        area2 = Area(name="Area Test 2")
        db.session.add(area1)
        db.session.add(area2)
        db.session.commit()

        # Crear plan con áreas
        plan = Plan(name="Plan Test", price=Decimal("100.00"))
        plan.areas = [area1, area2]
        db.session.add(plan)
        db.session.commit()

        # Registrar membresía
        membership = register_membership(
            client_id=client.id,
            plan_id=plan.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            area_ids=[area1.id, area2.id],
            contracted_price=Decimal("100.00"),
        )

        # Verificar snapshot
        assert membership.contracted_price == Decimal("100.00")
        assert len(membership.areas) == 2
        area_ids_in_membership = {area.id for area in membership.areas}
        assert area1.id in area_ids_in_membership
        assert area2.id in area_ids_in_membership

        # Modificar el plan original
        plan.name = "Plan Modificado"
        plan.price = Decimal("150.00")
        plan.areas = [area1]  # Eliminar area2
        db.session.commit()

        # Recargar membresía desde DB
        db.session.refresh(membership)

        # Verificar que la membresía conserva el snapshot original
        assert membership.contracted_price == Decimal("100.00")  # No cambió
        assert len(membership.areas) == 2  # No cambió
        area_ids_in_membership = {area.id for area in membership.areas}
        assert area1.id in area_ids_in_membership
        assert area2.id in area_ids_in_membership

        # Limpieza
        _cleanup_test_data(
            client_ids=[client.id],
            area_ids=[area1.id, area2.id],
            plan_ids=[plan.id],
            membership_ids=[membership.id],
        )


def test_renewal_continuity_preserves_areas_and_price(app):
    """Verifica que la renovación por continuidad preserve áreas y precio."""
    with app.app_context():
        ensure_test_database()

        # Crear datos
        cedula = generate_valid_cedula(20001)
        client = Client(cedula=cedula, first_name="Test", last_name="User", phone="0991234567")
        area = Area(name="Area Continuity")
        plan = Plan(name="Plan Continuity", price=Decimal("50.00"))
        plan.areas = [area]
        db.session.add(client)
        db.session.add(area)
        db.session.add(plan)
        db.session.commit()

        # Membresía original
        start_date = date(2024, 1, 15)
        end_date = date(2024, 2, 14)  # 1 mes exacto
        membership = register_membership(
            client_id=client.id,
            plan_id=plan.id,
            start_date=start_date,
            end_date=end_date,
            area_ids=[area.id],
            contracted_price=Decimal("50.00"),
        )

        # Renovar por continuidad
        renewed = renew_membership_continuity(
            membership_id=membership.id,
            area_ids=[area.id],
            contracted_price=Decimal("55.00"),  # Precio puede cambiar
        )

        # Verificar continuidad de fechas
        assert renewed.start_date == end_date + timedelta(days=1)  # Día siguiente
        assert renewed.end_date == date(2024, 3, 14)  # 1 mes después

        # Verificar que el precio y áreas se conservan si no se especifican
        assert renewed.contracted_price == Decimal("55.00")  # Nuevo precio
        assert len(renewed.areas) == 1
        assert renewed.areas[0].id == area.id

        # Limpieza
        _cleanup_test_data(
            client_ids=[client.id],
            area_ids=[area.id],
            plan_ids=[plan.id],
            membership_ids=[membership.id, renewed.id],
        )


def test_payment_uniqueness_prevents_double_payment(app):
    """Verifica que no se puedan registrar dos pagos para la misma membresía."""
    with app.app_context():
        ensure_test_database()

        # Crear datos
        cedula = generate_valid_cedula(20002)
        client = Client(cedula=cedula, first_name="Test", last_name="User", phone="0991234567")
        area = Area(name="Area Payment")
        plan = Plan(name="Plan Payment", price=Decimal("30.00"))
        plan.areas = [area]
        db.session.add(client)
        db.session.add(area)
        db.session.add(plan)
        db.session.commit()

        membership = register_membership(
            client_id=client.id,
            plan_id=plan.id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            area_ids=[area.id],
            contracted_price=Decimal("30.00"),
        )

        # Primer pago
        payment1 = register_payment(
            membership_id=membership.id,
            amount="30.00",
            payment_method="cash",
            payment_date=date.today(),
        )

        # Intentar segundo pago (debe fallar)
        with pytest.raises(Exception) as exc_info:
            register_payment(
                membership_id=membership.id,
                amount="30.00",
                payment_method="cash",
                payment_date=date.today(),
            )
        assert "pago" in str(exc_info.value).lower() or "duplicat" in str(exc_info.value).lower()

        # Limpieza
        _cleanup_test_data(
            client_ids=[client.id],
            area_ids=[area.id],
            plan_ids=[plan.id],
            membership_ids=[membership.id],
            payment_ids=[payment1.id],
        )


def test_cedula_collision_avoided_in_tests(app):
    """Verifica que el generador de cédulas evita colisiones."""
    with app.app_context():
        ensure_test_database()

        # Generar 100 cédulas y verificar que no haya duplicados
        cedulas = set()
        for i in range(100):
            cedula = generate_valid_cedula(30000 + i)
            assert cedula not in cedulas, f"Colisión de cédula detectada: {cedula}"
            cedulas.add(cedula)

        assert len(cedulas) == 100
