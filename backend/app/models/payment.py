"""Modelo de pagos de Active Gym."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Payment(db.Model):
    """Representa el pago completo de una membresía."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        Index(
            "ix_payments_transfer_reference_unique",
            "transfer_reference",
            unique=True,
            postgresql_where=text("transfer_reference IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    membership_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("memberships.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    payment_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    transfer_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    membership: Mapped["Membership"] = relationship(
        "Membership",
        back_populates="payment",
    )

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} "
            f"membership_id={self.membership_id} "
            f"amount={self.amount}>"
        )
