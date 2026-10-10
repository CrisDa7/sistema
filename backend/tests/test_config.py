"""
Configuración aislada para las pruebas de Active Gym.
"""

from sqlalchemy.engine import make_url

from app.config import Config


class TestConfig(Config):
    """Configuración exclusiva para pruebas."""

    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def get_test_database_uri():
        """
        Construye la conexión a la base de pruebas
        sin modificar la conexión de desarrollo.
        """

        development_uri = Config.SQLALCHEMY_DATABASE_URI

        if not development_uri:
            raise RuntimeError(
                "DATABASE_URL no está configurada."
            )

        development_url = make_url(development_uri)

        if development_url.get_backend_name() != "postgresql":
            raise RuntimeError(
                "Las pruebas requieren PostgreSQL."
            )

        if development_url.database != "active_gym_db":
            raise RuntimeError(
                "La base de desarrollo no es la esperada."
            )

        test_url = development_url.set(
            database="active_gym_test_db"
        )

        return test_url.render_as_string(
            hide_password=False
        )

    SQLALCHEMY_DATABASE_URI = get_test_database_uri()