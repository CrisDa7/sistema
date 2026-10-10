"""
Módulo de verificación del estado de la API de Active Gym.

Este módulo define un endpoint HTTP que permite comprobar
si la aplicación Flask está funcionando correctamente.

Endpoint:
    GET /api/health
"""

from flask import Blueprint, jsonify


# Blueprint encargado de agrupar las rutas de verificación.
health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    """
    Comprueba que la API se encuentra disponible.

    Returns:
        tuple:
            - Respuesta JSON con el estado de la aplicación.
            - Código HTTP 200 (OK).
    """
    return jsonify({
        "status": "ok",
        "message": "Active Gym API funcionando correctamente"
    }), 200