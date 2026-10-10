"""
Paquete principal del backend de Active Gym.

Contiene la fábrica de aplicación Flask y registra
los componentes necesarios para su funcionamiento.
"""

from flask import Flask

from app.routes.health import health_bp


def create_app():
    """
    Crea y configura una instancia de la aplicación Flask.

    Este patrón permite centralizar la configuración y
    registrar los Blueprints de manera organizada.

    Returns:
        Flask: Instancia configurada de la aplicación.
    """

    # Crear la instancia principal de Flask.
    app = Flask(__name__)

    # Registrar las rutas de verificación bajo el prefijo /api.
    app.register_blueprint(health_bp, url_prefix="/api")

    # Devolver la aplicación configurada.
    return app