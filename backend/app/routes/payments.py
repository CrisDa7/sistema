"""Blueprint REST para el módulo de pagos."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models.membership import Membership
from app.services.payment_service import (
    DuplicatePaymentError,
    DuplicateTransferReferenceError,
    MembershipNotFoundForPaymentError,
    get_payment_by_id,
    get_payment_for_membership,
    list_payments_by_membership,
    register_payment,
)

payments_bp = Blueprint("payments", __name__)


def serialize_payment(payment) -> dict:
    """Serializa un pago a JSON."""
    return {
        "id": payment.id,
        "membership_id": payment.membership_id,
        "amount": str(payment.amount),
        "payment_method": payment.payment_method,
        "payment_date": payment.payment_date.isoformat(),
        "created_at": payment.created_at.isoformat() if hasattr(payment.created_at, "isoformat") else None,
        "transfer_reference": payment.transfer_reference,
        "observations": payment.observations,
    }


@payments_bp.post("/memberships/<int:membership_id>/payments")
def create_membership_payment(membership_id: int):
    """Registra el pago completo de una membresía."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    try:
        payment_date = date.fromisoformat(data.get("payment_date"))
        payment = register_payment(
            membership_id=membership_id,
            amount=data.get("amount"),
            payment_method=data.get("payment_method"),
            payment_date=payment_date,
            transfer_reference=data.get("transfer_reference"),
            observations=data.get("observations"),
        )
    except MembershipNotFoundForPaymentError as exc:
        return jsonify({"error": str(exc)}), 404
    except DuplicatePaymentError as exc:
        return jsonify({"error": str(exc)}), 409
    except DuplicateTransferReferenceError as exc:
        return jsonify({"error": str(exc)}), 409
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error inesperado al registrar pago")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_payment(payment)), 201


@payments_bp.get("/memberships/<int:membership_id>/payments")
def get_membership_payments(membership_id: int):
    """Lista los pagos de una membresía."""
    membership = db.session.get(Membership, membership_id)
    if membership is None:
        return jsonify({"error": "La membresía no existe."}), 404

    return jsonify([serialize_payment(item) for item in list_payments_by_membership(membership_id)]), 200


@payments_bp.get("/payments/<int:payment_id>")
def get_payment(payment_id: int):
    """Obtiene un pago por su identificador."""
    payment = get_payment_by_id(payment_id)
    if payment is None:
        return jsonify({"error": "El pago no existe."}), 404
    return jsonify(serialize_payment(payment)), 200


@payments_bp.get("/memberships/<int:membership_id>/payment-status")
def get_payment_status(membership_id: int):
    """Devuelve si la membresía ya fue pagada y el precio contratado."""
    membership = db.session.get(Membership, membership_id)
    if membership is None:
        return jsonify({"error": "La membresía no existe."}), 404

    payment = get_payment_for_membership(membership_id)
    return jsonify(
        {
            "membership_id": membership.id,
            "contracted_price": str(membership.contracted_price),
            "paid": payment is not None,
            "payment_id": payment.id if payment is not None else None,
        }
    ), 200
