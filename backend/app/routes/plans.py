"""Blueprint REST para el módulo de planes de Active Gym."""

from __future__ import annotations

from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.services.plan_service import (
    AreaNotFoundForPlanError,
    DuplicatePlanError,
    PlanNotFoundError,
    get_plan_by_id,
    list_plans,
    register_plan,
    update_plan,
)

plans_bp = Blueprint("plans", __name__)


def serialize_plan(plan) -> dict:
    """Serializa un plan a un diccionario JSON seguro."""
    return {
        "id": plan.id,
        "name": plan.name,
        "price": str(plan.price),
        "is_active": plan.is_active,
        "areas": [
            {"id": area.id, "name": area.name}
            for area in plan.areas
        ],
    }


@plans_bp.post("/plans")
def create_plan():
    """Registra un plan nuevo. Requiere autenticación antes de producción."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    try:
        plan = register_plan(
            name=data.get("name", ""),
            price=data.get("price", ""),
            area_ids=data.get("area_ids"),
        )
    except DuplicatePlanError as exc:
        return jsonify({"error": str(exc)}), 409
    except (AreaNotFoundForPlanError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error inesperado al crear plan")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_plan(plan)), 201


@plans_bp.get("/plans")
def get_plans():
    """Lista todos los planes."""
    return jsonify([serialize_plan(plan) for plan in list_plans()]), 200


@plans_bp.get("/plans/<int:plan_id>")
def get_plan(plan_id: int):
    """Obtiene un plan por su identificador."""
    plan = get_plan_by_id(plan_id)
    if plan is None:
        return jsonify({"error": "Plan no encontrado."}), 404
    return jsonify(serialize_plan(plan)), 200


@plans_bp.patch("/plans/<int:plan_id>")
def patch_plan(plan_id: int):
    """Actualiza un plan existente."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    try:
        plan = update_plan(
            plan_id,
            name=data.get("name"),
            price=data.get("price"),
            area_ids=data.get("area_ids"),
        )
    except PlanNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except DuplicatePlanError as exc:
        return jsonify({"error": str(exc)}), 409
    except (AreaNotFoundForPlanError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error inesperado al actualizar plan")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_plan(plan)), 200
