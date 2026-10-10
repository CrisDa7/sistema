"""Blueprint REST para el módulo de áreas de Active Gym."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.services.area_service import (
    AreaNotFoundError,
    DuplicateAreaError,
    get_area_by_id,
    list_areas,
    register_area,
    update_area,
)

areas_bp = Blueprint("areas", __name__)


def serialize_area(area) -> dict:
    """Serializa un área a un diccionario JSON seguro."""
    return {
        "id": area.id,
        "name": area.name,
        "is_active": area.is_active,
    }


@areas_bp.post("/areas")
def create_area():
    """Registra una nueva área. Requiere autenticación antes de producción."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    try:
        area = register_area(data.get("name", ""))
    except DuplicateAreaError as exc:
        return jsonify({"error": str(exc)}), 409
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error inesperado al crear área")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_area(area)), 201


@areas_bp.get("/areas")
def get_areas():
    """Lista todas las áreas."""
    return jsonify([serialize_area(area) for area in list_areas()]), 200


@areas_bp.get("/areas/<int:area_id>")
def get_area(area_id: int):
    """Obtiene un área por su identificador."""
    area = get_area_by_id(area_id)
    if area is None:
        return jsonify({"error": "Área no encontrada."}), 404
    return jsonify(serialize_area(area)), 200


@areas_bp.patch("/areas/<int:area_id>")
def patch_area(area_id: int):
    """Actualiza un área existente."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    try:
        area = update_area(area_id, name=data.get("name"))
    except AreaNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except DuplicateAreaError as exc:
        return jsonify({"error": str(exc)}), 409
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error inesperado al actualizar área")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_area(area)), 200
