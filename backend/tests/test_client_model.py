"""
Pruebas unitarias del modelo Client de Active Gym.

Verifica la definición de los campos y las restricciones
del modelo sin crear tablas ni modificar PostgreSQL.
"""

from datetime import date

from app import create_app
from app.extensions import db
from app.models import Client


def test_client_table_structure():
    """
    Comprueba la estructura básica del modelo Client.

    Verifica:
        - Nombre de la tabla.
        - Columnas registradas.
        - Clave primaria.
        - Campos obligatorios.
    """

    app = create_app()

    with app.app_context():
        table = db.metadata.tables["clients"]

        expected_columns = {
            "id",
            "cedula",
            "first_name",
            "last_name",
            "phone",
            "registration_date",
        }

        # Comprobar que las columnas coinciden con el diseño.
        assert set(table.columns.keys()) == expected_columns

        # El identificador debe ser la clave primaria.
        assert table.c.id.primary_key

        # Los datos principales son obligatorios.
        assert not table.c.first_name.nullable
        assert not table.c.last_name.nullable
        assert not table.c.phone.nullable
        assert not table.c.registration_date.nullable


def test_client_creation():
    """
    Comprueba que es posible construir un objeto Client.

    Esta prueba no guarda registros en PostgreSQL.
    """

    client = Client(
        cedula="1101234567",
        first_name="Ana",
        last_name="Lopez",
        phone="0991234567",
    )

    assert client.first_name == "Ana"
    assert client.last_name == "Lopez"
    assert client.phone == "0991234567"


def test_client_registration_date_default():
    """
    Verifica la configuración de la fecha predeterminada.

    Comprueba que SQLAlchemy dispone de una función
    invocable para generar la fecha de registro.

    No inserta registros en PostgreSQL.
    """

    # Obtener la columna de fecha del modelo Client.
    column = Client.__table__.c.registration_date

    # Comprobar que existe un valor predeterminado.
    assert column.default is not None

    # Verificar que el valor se genera mediante una función.
    assert column.default.is_callable


def test_client_cedula_structure():
    """Comprueba la configuración del campo cédula."""

    cedula_column = Client.__table__.columns["cedula"]

    assert cedula_column.type.length == 10
    assert cedula_column.nullable is False
    assert cedula_column.unique is True
    assert cedula_column.index is True