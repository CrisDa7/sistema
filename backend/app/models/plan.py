"""
Modelos de planes comerciales de Active Gym.

Define los planes disponibles y su relación de muchos
a muchos con las áreas deportivas del gimnasio.
"""

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


# Tabla intermedia para relacionar planes con áreas.
# La clave primaria compuesta evita asociaciones duplicadas.
plan_areas = Table(
    "plan_areas",
    db.metadata,
    Column(
        "plan_id",
        Integer,
        ForeignKey("plans.id"),
        primary_key=True,
    ),
    Column(
        "area_id",
        Integer,
        ForeignKey("areas.id"),
        primary_key=True,
    ),
)


class Plan(db.Model):
    """
    Representa un plan comercial del gimnasio.

    Attributes:
        id: Identificador único del plan.
        name: Nombre comercial.
        price: Precio configurado del plan.
        is_active: Indica si puede ofrecerse.
        areas: Áreas deportivas incluidas.
    """

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # Nombre obligatorio y único del plan.
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    # Decimal evita errores de precisión de los float.
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    # Permite retirar un plan sin borrar su historial.
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Un plan puede contener varias áreas.
    areas: Mapped[list["Area"]] = relationship(
        "Area",
        secondary=plan_areas,
        backref="plans",
    )

    def __repr__(self) -> str:
        """
        Devuelve una representación útil para depuración.
        """
        return f"<Plan id={self.id} name='{self.name}'>"