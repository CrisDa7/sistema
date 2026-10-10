"""
Pruebas unitarias del modelo Membership.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import inspect

from app.models import Area, Membership, membership_areas


def test_membership_table_structure():
    """Verifica los campos principales del modelo."""

    mapper = inspect(Membership)
    columns = mapper.columns

    assert Membership.__tablename__ == "memberships"

    assert "id" in columns
    assert "client_id" in columns
    assert "plan_id" in columns
    assert "start_date" in columns
    assert "end_date" in columns
    assert "contracted_price" in columns

    assert columns["client_id"].nullable is False
    assert columns["plan_id"].nullable is False
    assert columns["contracted_price"].nullable is False


def test_membership_foreign_keys():
    """Verifica las referencias al cliente y al plan."""

    columns = inspect(Membership).columns

    client_fk = next(
        iter(columns["client_id"].foreign_keys)
    )

    plan_fk = next(
        iter(columns["plan_id"].foreign_keys)
    )

    assert client_fk.target_fullname == "clients.id"
    assert plan_fk.target_fullname == "plans.id"


def test_membership_creation():
    """Verifica la creación de una membresía en memoria."""

    membership = Membership(
        client_id=1,
        plan_id=1,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 11, 9),
        contracted_price=Decimal("30.00"),
    )

    assert membership.client_id == 1
    assert membership.plan_id == 1

    assert membership.start_date == date(2026, 10, 10)
    assert membership.end_date == date(2026, 11, 9)

    assert membership.contracted_price == Decimal("30.00")


def test_membership_areas_table_structure():
    """Verifica la tabla intermedia de membresías y áreas."""

    assert membership_areas.name == "membership_areas"

    columns = membership_areas.columns

    assert "membership_id" in columns
    assert "area_id" in columns

    assert columns["membership_id"].primary_key
    assert columns["area_id"].primary_key


def test_membership_creation_with_areas():
    """Verifica que una membresía conserve sus propias áreas."""

    musculacion = Area(name="Musculación")
    jumping = Area(name="Jumping")

    membership = Membership(
        client_id=1,
        plan_id=1,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 11, 9),
        contracted_price=Decimal("30.00"),
        areas=[musculacion, jumping],
    )

    assert len(membership.areas) == 2
    assert musculacion in membership.areas
    assert jumping in membership.areas