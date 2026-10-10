"""Blueprint REST para el módulo de membresías."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.services.membership_service import (
    AreaNotFoundForMembershipError,
    ClientNotFoundForMembershipError,
    MembershipConflictError,
    MembershipNotFoundError,
    PlanNotFoundForMembershipError,
    calculate_membership_status,
    calculate_reminder_date,
    get_membership_by_id,
    list_memberships,
    list_memberships_by_client,
    register_membership,
    register_reentry_membership,
    renew_membership_continuity,
)

memberships_bp = Blueprint("memberships", __name__)


def serialize_membership(membership) -> dict:
    """Serializa una membresía a salida JSON."""
    return {
        "id": membership.id,
        "client_id": membership.client_id,
        "plan_id": membership.plan_id,
        "start_date": membership.start_date.isoformat(),
        "end_date": membership.end_date.isoformat(),
        "contracted_price": str(membership.contracted_price),
        "areas": [
            {"id": area.id, "name": area.name}
            for area in membership.areas
        ],
        "status": calculate_membership_status(membership),
        "reminder_date": calculate_reminder_date(membership).isoformat(),
    }


@memberships_bp.post("/memberships")
def create_membership():
    """Registra una nueva membresía."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    try:
        start_date = date.fromisoformat(data.get("start_date"))
        end_date = date.fromisoformat(data.get("end_date"))
        membership = register_membership(
            client_id=int(data.get("client_id")),
            plan_id=int(data.get("plan_id")),
            start_date=start_date,
            end_date=end_date,
            area_ids=data.get("area_ids", []),
            contracted_price=data.get("contracted_price"),
        )
    except ClientNotFoundForMembershipError as exc:
        return jsonify({"error": str(exc)}), 404
    except PlanNotFoundForMembershipError as exc:
        return jsonify({"error": str(exc)}), 404
    except AreaNotFoundForMembershipError as exc:
        return jsonify({"error": str(exc)}), 400
    except MembershipConflictError as exc:
        return jsonify({"error": str(exc)}), 409
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error inesperado al crear membresía")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_membership(membership)), 201


@memberships_bp.get("/memberships")
def get_memberships():
    """Lista todas las membresías."""
    return jsonify([serialize_membership(item) for item in list_memberships()]), 200


@memberships_bp.get("/memberships/<int:membership_id>")
def get_membership(membership_id: int):
    """Obtiene una membresía por ID."""
    membership = get_membership_by_id(membership_id)
    if membership is None:
        return jsonify({"error": "Membresía no encontrada."}), 404
    return jsonify(serialize_membership(membership)), 200


@memberships_bp.get("/clients/<int:client_id>/memberships")
def get_client_memberships(client_id: int):
    """Obtiene las membresías de un cliente."""
    memberships = list_memberships_by_client(client_id)
    return jsonify([serialize_membership(item) for item in memberships]), 200


@memberships_bp.post("/memberships/<int:membership_id>/renew")
def renew_membership(membership_id: int):
    """Renueva una membresía previa como continuidad o reingreso."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    mode = data.get("mode")
    if mode not in {"continuity", "reentry"}:
        return jsonify({"error": "El modo de renovación debe ser 'continuity' o 'reentry'."}), 400

    try:
        if mode == "continuity":
            membership = renew_membership_continuity(
                membership_id=membership_id,
                renewal_date=date.today(),
                area_ids=data.get("area_ids"),
                contracted_price=data.get("contracted_price"),
            )
        else:
            start_date = date.fromisoformat(data.get("start_date"))
            membership = register_reentry_membership(
                client_id=get_membership_by_id(membership_id).client_id,
                plan_id=get_membership_by_id(membership_id).plan_id,
                start_date=start_date,
                end_date=None,
                area_ids=data.get("area_ids"),
                contracted_price=data.get("contracted_price"),
                previous_membership_id=membership_id,
            )
    except MembershipNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except (AreaNotFoundForMembershipError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except MembershipConflictError as exc:
        return jsonify({"error": str(exc)}), 409
    except Exception:
        current_app.logger.exception("Error inesperado al renovar membresía")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_membership(membership)), 201
