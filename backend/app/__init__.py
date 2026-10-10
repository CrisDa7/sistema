"""
Paquete principal del backend de Active Gym.

Implementa el patrón Application Factory y centraliza
la configuración de Flask, sus extensiones y sus rutas.
"""

from flask import Flask

from app.config import Config
from app.extensions import db, migrate
from app.routes.health import health_bp


def create_app(config_class=Config):
    """
    Crea y configura una instancia de Flask.

    Args:
        config_class:
            Clase de configuración que utilizará la aplicación.
            Por defecto se utiliza Config.

    Returns:
        Flask:
            Instancia configurada de la aplicación.
    """

    # Crear la instancia principal de Flask.
    app = Flask(__name__)

    # Cargar la configuración de la aplicación.
    app.config.from_object(config_class)

    # Inicializar SQLAlchemy con la aplicación Flask.
    db.init_app(app)

    # Inicializar el gestor de migraciones.
    migrate.init_app(app, db)

    # Registrar el Blueprint de verificación.
    app.register_blueprint(health_bp, url_prefix="/api")

    return app