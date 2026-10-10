"""
Modelo de membresías de Active Gym.

Representa la contratación de un plan por parte
de un cliente, conservando las fechas y el precio
acordados al momento de la contratación.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

membership_areas = Table(
    "membership_areas",
    db.metadata,

    Column(
        "membership_id",
        Integer,
        ForeignKey("memberships.id"),
        primary_key=True,
    ),

    Column(
        "area_id",
        Integer,
        ForeignKey("areas.id"),
        primary_key=True,
    ),
)

class Membership(db.Model):
    """Representa una membresía contratada por un cliente."""

    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id"),
        nullable=False,
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("plans.id"),
        nullable=False,
    )

    areas: Mapped[list["Area"]] = relationship(
    "Area",
    secondary=membership_areas,
    backref="memberships",
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    contracted_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    client: Mapped["Client"] = relationship(
        "Client",
        backref="memberships",
    )

    plan: Mapped["Plan"] = relationship(
        "Plan",
        backref="memberships",
    )

    payment: Mapped["Payment | None"] = relationship(
        "Payment",
        back_populates="membership",
        uselist=False,
    )

    def __repr__(self) -> str:
        """Devuelve una representación útil para depuración."""
        return (
            f"<Membership id={self.id} "
            f"client_id={self.client_id} "
            f"plan_id={self.plan_id}>"
        )