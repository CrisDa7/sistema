"""Servicios para la gestión de pagos de Active Gym."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.membership import Membership
from app.models.payment import Payment


class PaymentError(ValueError):
    """Error base del dominio de pagos."""


class MembershipNotFoundForPaymentError(PaymentError):
    """Se lanza cuando la membresía asociada no existe."""


class DuplicatePaymentError(PaymentError):
    """Se lanza cuando una membresía ya tiene un pago registrado."""


class DuplicateTransferReferenceError(PaymentError):
    """Se lanza cuando la referencia bancaria ya fue usada."""


def _normalize_payment_amount(value: object) -> Decimal:
    """Valida y normaliza un monto de pago."""
    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, (int, float, str)):
        try:
            amount = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError("El monto del pago debe ser un número válido.") from exc
    else:
        raise ValueError("El monto del pago debe ser un número válido.")

    if amount <= 0:
        raise ValueError("El monto del pago debe ser mayor a cero.")

    return amount.quantize(Decimal("0.01"))


def _normalize_transfer_reference(value: object) -> str:
    """Normaliza la referencia bancaria para evitar duplicados por formato."""
    if value is None:
        raise ValueError("La referencia de transferencia es obligatoria para pagos bancarios.")

    text_value = str(value).strip()
    if not text_value:
        raise ValueError("La referencia de transferencia es obligatoria para pagos bancarios.")

    return re.sub(r"\s+", "", text_value).upper()


def get_payment_by_id(payment_id: int) -> Payment | None:
    """Obtiene un pago por su identificador."""
    return db.session.get(Payment, payment_id)


def list_payments_by_membership(membership_id: int) -> list[Payment]:
    """Lista los pagos de una membresía."""
    return list(
        db.session.execute(
            select(Payment)
            .where(Payment.membership_id == membership_id)
            .order_by(Payment.id.desc())
        ).scalars().all()
    )


def get_payment_for_membership(membership_id: int) -> Payment | None:
    """Devuelve el único pago registrado para una membresía, si existe."""
    return db.session.execute(
        select(Payment)
        .where(Payment.membership_id == membership_id)
        .limit(1)
    ).scalar_one_or_none()


def get_payment_status(membership_id: int) -> dict:
    """Devuelve el estado de pago de una membresía."""
    membership = db.session.get(Membership, membership_id)
    if membership is None:
        raise MembershipNotFoundForPaymentError("La membresía no existe.")

    payment = get_payment_for_membership(membership_id)
    return {
        "membership_id": membership.id,
        "contracted_price": str(membership.contracted_price.quantize(Decimal("0.01"))),
        "paid": payment is not None,
        "payment_id": payment.id if payment is not None else None,
    }


def register_payment(
    membership_id: int,
    amount: Decimal | int | float | str,
    payment_method: str,
    payment_date: date,
    transfer_reference: str | None = None,
    observations: str | None = None,
) -> Payment:
    """Registra un pago completo para una membresía, validando duplicados y montos."""
    if not isinstance(membership_id, int):
        raise MembershipNotFoundForPaymentError("La membresía es obligatoria.")

    membership = db.session.get(Membership, membership_id)
    if membership is None:
        raise MembershipNotFoundForPaymentError("La membresía no existe.")

    if not isinstance(payment_method, str):
        raise ValueError("El método de pago es obligatorio.")

    normalized_method = payment_method.strip().lower()
    if normalized_method not in {"cash", "bank_transfer"}:
        raise ValueError("El método de pago debe ser 'cash' o 'bank_transfer'.")

    if not isinstance(payment_date, date):
        raise ValueError("La fecha real del pago debe ser válida.")

    if get_payment_for_membership(membership_id) is not None:
        raise DuplicatePaymentError("Esta membresía ya tiene un pago registrado.")

    normalized_amount = _normalize_payment_amount(amount)
    if normalized_amount != membership.contracted_price.quantize(Decimal("0.01")):
        raise ValueError(
            "El monto del pago debe coincidir exactamente con el precio contratado de la membresía."
        )

    if normalized_method == "bank_transfer":
        normalized_reference = _normalize_transfer_reference(transfer_reference)
        existing_reference = db.session.execute(
            select(Payment)
            .where(Payment.payment_method == "bank_transfer")
            .where(Payment.transfer_reference == normalized_reference)
            .limit(1)
        ).scalar_one_or_none()

        if existing_reference is not None:
            raise DuplicateTransferReferenceError(
                "La referencia bancaria ya está registrada en otro pago."
            )

        effective_reference = normalized_reference
    else:
        if transfer_reference is not None and str(transfer_reference).strip() != "":
            raise ValueError("Para pagos en efectivo la referencia de transferencia debe ser nula.")
        effective_reference = None

    payment = Payment(
        membership_id=membership.id,
        amount=normalized_amount,
        payment_method=normalized_method,
        payment_date=payment_date,
        transfer_reference=effective_reference,
        observations=observations.strip() if isinstance(observations, str) and observations.strip() else None,
    )

    try:
        db.session.add(payment)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        if "uq_payments_membership_id" in str(exc) or "payments_membership_id_key" in str(exc):
            raise DuplicatePaymentError("Esta membresía ya tiene un pago registrado.") from exc
        if "ix_payments_transfer_reference_unique" in str(exc):
            raise DuplicateTransferReferenceError(
                "La referencia bancaria ya está registrada en otro pago."
            ) from exc
        raise PaymentError("No se pudo registrar el pago por un conflicto de integridad.") from exc

    return payment
