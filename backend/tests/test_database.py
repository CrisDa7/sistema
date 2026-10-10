"""
Pruebas de integración de la base de datos de Active Gym.

Verifica que la aplicación Flask puede establecer
una conexión real con PostgreSQL utilizando SQLAlchemy.

Estas pruebas requieren una base de datos de desarrollo
configurada y disponible.
"""

from sqlalchemy import text

from app import create_app
from app.extensions import db


def test_database_connection():
    """
    Comprueba la conexión de Flask con PostgreSQL.

    Verifica que:
        - La aplicación puede ejecutar una consulta SQL.
        - PostgreSQL devuelve el nombre de la base de datos.
        - La conexión corresponde a active_gym_db.
    """

    # Crear una instancia de la aplicación Flask.
    app = create_app()

    # Activar el contexto necesario para utilizar SQLAlchemy.
    with app.app_context():

        # Ejecutar una consulta de solo lectura.
        result = db.session.execute(
            text("SELECT current_database()")
        )

        # Obtener el nombre de la base de datos conectada.
        database_name = result.scalar()

        # Comprobar que utilizamos la base de datos esperada.
        assert database_name == "active_gym_db"