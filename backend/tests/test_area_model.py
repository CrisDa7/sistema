"""
Pruebas unitarias del modelo Area de Active Gym.

Comprueba su estructura y configuración sin realizar
operaciones de escritura en PostgreSQL.
"""

from app import create_app
from app.extensions import db
from app.models import Area


def test_area_table_structure():
    """
    Verifica las columnas y restricciones del área.
    """

    app = create_app()

    with app.app_context():
        table = db.metadata.tables["areas"]

        expected_columns = {
            "id",
            "name",
            "is_active",
        }

        assert set(table.columns.keys()) == expected_columns

        # Verificar la clave primaria.
        assert table.c.id.primary_key

        # Verificar que los campos son obligatorios.
        assert not table.c.name.nullable
        assert not table.c.is_active.nullable

        # Evitar nombres exactamente duplicados.
        assert table.c.name.unique


def test_area_creation():
    """
    Verifica que podemos construir un objeto Area.

    No guarda información en PostgreSQL.
    """

    area = Area(name="Musculación")

    assert area.name == "Musculación"


def test_area_active_by_default():
    """
    Verifica que las nuevas áreas tienen configurado
    el estado activo como valor predeterminado.
    """

    column = Area.__table__.c.is_active

    assert column.default is not None
    assert column.default.arg is True