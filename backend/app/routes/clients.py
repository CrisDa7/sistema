"""Blueprint REST para el módulo de clientes de Active Gym."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.services.client_service import (
    ClientNotFoundError,
    DuplicateCedulaError,
    get_client_by_id,
    list_clients,
    register_client,
    search_clients,
    update_client,
)

clients_bp = Blueprint("clients", __name__)


def serialize_client(client) -> dict:
    """Serializa un cliente a un diccionario JSON seguro."""
    return {
        "id": client.id,
        "cedula": client.cedula,
        "first_name": client.first_name,
        "last_name": client.last_name,
        "phone": client.phone,
        "registration_date": client.registration_date.isoformat(),
    }


@clients_bp.post("/clients")
def create_client():
    """Registra un cliente nuevo. Requiere autenticación antes de producción."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    try:
        client = register_client(
            cedula=data.get("cedula", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            phone=data.get("phone", ""),
        )
    except DuplicateCedulaError as exc:
        return jsonify({"error": str(exc)}), 409
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error inesperado al crear cliente")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_client(client)), 201


@clients_bp.get("/clients")
def get_clients():
    """Lista todos los clientes o aplica una búsqueda por texto."""
    search = request.args.get("search", type=str)
    clients = search_clients(search) if search else list_clients()

    return jsonify([serialize_client(client) for client in clients]), 200


@clients_bp.get("/clients/<int:client_id>")
def get_client(client_id: int):
    """Obtiene un cliente por su identificador interno."""
    client = get_client_by_id(client_id)
    if client is None:
        return jsonify({"error": "Cliente no encontrado."}), 404

    return jsonify(serialize_client(client)), 200


@clients_bp.patch("/clients/<int:client_id>")
def patch_client(client_id: int):
    """Actualiza únicamente los campos editables del cliente. Requiere autenticación antes de producción."""
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    try:
        client = update_client(client_id, **data)
    except ClientNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        current_app.logger.exception("Error inesperado al actualizar cliente")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500

    return jsonify(serialize_client(client)), 200
