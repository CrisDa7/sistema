"""
Configuración principal del backend de Active Gym.

Centraliza los parámetros de configuración y carga
las variables de entorno necesarias para la aplicación.
"""

import os

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