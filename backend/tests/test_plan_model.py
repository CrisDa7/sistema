"""
Pruebas unitarias del modelo Plan de Active Gym.

Verifica los campos y la relación entre planes y áreas
sin realizar operaciones en PostgreSQL.
"""

from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import Area, Plan


def test_plan_table_structure():
    """
    Comprueba la estructura del modelo Plan.
    """

    app = create_app()

    with app.app_context():
        table = db.metadata.tables["plans"]

        expected_columns = {
            "id",
            "name",
            "price",
            "is_active",
        }

        assert set(table.columns.keys()) == expected_columns
        assert table.c.id.primary_key
        assert table.c.name.unique
        assert not table.c.price.nullable
        assert not table.c.is_active.nullable


def test_plan_areas_relationship():
    """
    Comprueba la tabla intermedia de planes y áreas.

    La clave primaria compuesta impide repetir
    exactamente la misma asociación.
    """

    app = create_app()

    with app.app_context():
        table = db.metadata.tables["plan_areas"]

        assert set(table.columns.keys()) == {
            "plan_id",
            "area_id",
        }

        assert table.c.plan_id.primary_key
        assert table.c.area_id.primary_key

        assert len(table.foreign_keys) == 2


def test_plan_creation_with_areas():
    """
    Construye un plan con dos áreas sin guardarlo
    en PostgreSQL.
    """

    musculacion = Area(name="Musculación")
    jumping = Area(name="Jumping")

    plan = Plan(
        name="Musculación + Jumping",
        price=Decimal("30.00"),
        areas=[musculacion, jumping],
    )

    assert plan.name == "Musculación + Jumping"
    assert plan.price == Decimal("30.00")
    assert len(plan.areas) == 2
    assert musculacion in plan.areas
    assert jumping in plan.areas