"""Rutas de autenticación administrativa para Active Gym."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session

from app.extensions import db
from app.services.admin_service import (
    AdminLimitReachedError,
    BruteForceLockError,
    CSRFTokenError,
    InvalidCredentialsError,
    SessionExpiredError,
    SessionRevokedError,
    authenticate_admin,
    generate_csrf_token,
    get_current_admin,
    get_csrf_token,
    issue_session_for_admin,
    require_admin_auth,
    revoke_current_session,
    validate_csrf_token,
)

admin_auth_bp = Blueprint("admin_auth", __name__)


@admin_auth_bp.get("/auth/csrf")
def get_csrf():
    """Retorna un token CSRF para la sesión actual."""
    csrf_token = generate_csrf_token()
    session["csrf_token"] = csrf_token
    return jsonify({"csrf_token": csrf_token}), 200


@admin_auth_bp.post("/auth/login")
def login_admin():
    """Inicia sesión del administrador y crea una sesión segura en cookie."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "El cuerpo de la solicitud debe ser un JSON válido."}), 400

    csrf_token = data.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        return jsonify({"error": "Token CSRF inválido."}), 403

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    try:
        admin = authenticate_admin(username, password)
        session_id = issue_session_for_admin(admin)
        session["session_id"] = session_id
        session["admin_id"] = admin.id
        session["csrf_token"] = generate_csrf_token()
        session.permanent = True
        current_app.permanent_session_lifetime = 60 * 60 * 8
        return jsonify({
            "message": "Sesión iniciada correctamente.",
            "admin": {"id": admin.id, "username": admin.username},
        }), 200
    except BruteForceLockError as exc:
        return jsonify({"error": str(exc)}), 429
    except InvalidCredentialsError as exc:
        return jsonify({"error": str(exc)}), 401
    except Exception:
        current_app.logger.exception("Error inesperado durante el login")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500


@admin_auth_bp.post("/auth/logout")
def logout_admin():
    """Cierra la sesión del administrador y la revoca en PostgreSQL."""
    data = request.get_json(silent=True) or {}
    csrf_token = request.headers.get("X-CSRF-Token") or data.get("csrf_token")
    if not validate_csrf_token(csrf_token):
        return jsonify({"error": "Token CSRF inválido."}), 403

    try:
        revoke_current_session()
        return jsonify({"message": "Sesión cerrada correctamente."}), 200
    except Exception:
        current_app.logger.exception("Error inesperado durante el logout")
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor."}), 500


@admin_auth_bp.get("/auth/session")
def get_session_status():
    """Devuelve el estado actual de la sesión del administrador."""
    try:
        admin = get_current_admin()
        if admin is None:
            return jsonify({"authenticated": False}), 200

        return jsonify({
            "authenticated": True,
            "admin": {"id": admin.id, "username": admin.username},
        }), 200
    except SessionExpiredError as exc:
        return jsonify({"authenticated": False, "error": str(exc)}), 401
    except SessionRevokedError as exc:
        return jsonify({"authenticated": False, "error": str(exc)}), 401


@admin_auth_bp.before_request
def enforce_admin_auth_for_admin_routes():
    """Protege por defecto los endpoints administrativos salvo el health y auth public."""
    if request.endpoint in {"health.health_check", "admin_auth.get_csrf", "admin_auth.login_admin"}:
        return None

    if request.endpoint.startswith("admin_auth."):
        if request.path.endswith("/auth/session"):
            return None

    try:
        require_admin_auth()
    except PermissionError:
        return jsonify({"error": "Autenticación requerida."}), 401
    except SessionExpiredError:
        return jsonify({"error": "La sesión ha expirado."}), 401
    except SessionRevokedError:
        return jsonify({"error": "La sesión ha sido revocada."}), 401
