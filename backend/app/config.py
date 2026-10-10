"""
Configuración principal del backend de Active Gym.

Centraliza los parámetros de configuración y carga
las variables de entorno necesarias para la aplicación.
"""

import os
import secrets

from dotenv import load_dotenv


# Cargar las variables definidas en el archivo .env.
# No sobrescribe variables de entorno existentes.
load_dotenv()


class Config:
    """
    Configuración base de Flask y SQLAlchemy.

    La dirección de conexión se obtiene desde DATABASE_URL
    para evitar almacenar credenciales dentro del código.
    """

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    # Desactivar el seguimiento adicional de modificaciones.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de cookies para desarrollo (HTTP)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"

    # SECRET_KEY se establece dinámicamente en create_app
    SECRET_KEY = None


class ProductionConfig(Config):
    """
    Configuración para producción con seguridad reforzada.

    Requiere HTTPS y variables de entorno configuradas.
    """

    # En producción, SECRET_KEY debe provenir obligatoriamente de variable de entorno
    # Se mantiene None aquí; create_app lo validará
    SECRET_KEY = None

    # Cookies seguras solo sobre HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Strict"

    # Opcional: forzar HTTPS
    # PREFERRED_URL_SCHEME = "https"