"""
Extensiones utilizadas por el backend de Active Gym.

Las extensiones se crean sin asociarlas inmediatamente
a una aplicación Flask para mantener la compatibilidad
con el patrón Application Factory.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


# Gestiona los modelos y las operaciones con la base de datos.
db = SQLAlchemy()

# Gestiona las migraciones del esquema de la base de datos.
migrate = Migrate()