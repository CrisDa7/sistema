"""
Modelo de áreas deportivas de Active Gym.

Representa las actividades o áreas que ofrece
el gimnasio y permite gestionar su disponibilidad.
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Area(db.Model):
    """
    Representa un área deportiva del gimnasio.

    Attributes:
        id: Identificador único del área.
        name: Nombre del área deportiva.
        is_active: Indica si el área está disponible.
    """

    __tablename__ = "areas"

    # Identificador único generado por la base de datos.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # Nombre obligatorio y único para evitar duplicados exactos.
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    # Permite desactivar áreas sin eliminar su historial.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    def __repr__(self) -> str:
        """
        Devuelve una representación legible del área.

        Returns:
            str: Identificador y nombre del área.
        """
        return f"<Area id={self.id} name='{self.name}'>"