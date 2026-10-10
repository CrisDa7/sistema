"""
Paquete principal del backend de Active Gym.

Implementa el patrón Application Factory y centraliza
la configuración de Flask, sus extensiones y sus rutas.
"""

from __future__ import annotations
from datetime import timedelta
import os
import secrets

import click
from flask import Blueprint, Flask, current_app, jsonify, request, session
from sqlalchemy import select, text

from app.config import Config
from app.extensions import db, migrate
from app.models import Admin, AdminLoginAttempt, AdminSession
from app.routes.admin_auth import admin_auth_bp
from app.routes.areas import areas_bp
from app.routes.clients import clients_bp
from app.routes.health import health_bp
from app.routes.memberships import memberships_bp
from app.routes.payments import payments_bp
from app.routes.plans import plans_bp
from app.services.admin_service import create_admin_account, require_admin_auth


def _validate_admin_password(password: str) -> None:
    """Valida la seguridad mínima de la contraseña del administrador."""
    if len(password) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres.")
    if password.isalpha() or password.isdigit():
        raise ValueError("La contraseña debe incluir letras y números o símbolos.")
    if password.strip() != password:
        raise ValueError("La contraseña no puede tener espacios al inicio o final.")


def _ensure_target_database(app: Flask) -> None:
    """Verifica que el comando se está ejecutando en la base correcta."""
    database_name = db.session.execute(text("SELECT current_database()")) .scalar_one()
    expected_database = "active_gym_test_db" if app.config.get("TESTING") else "active_gym_db"
    if database_name != expected_database:
        raise RuntimeError(
            "Operación bloqueada: la base de datos actual es "
            f"'{database_name}', se esperaba '{expected_database}'."
        )


def _ensure_auth_tables(app: Flask) -> None:
    """Crea solo las tablas de autenticación necesarias en active_gym_test_db."""
    if not app.config.get("TESTING"):
        return

    from tests.db_safety import ensure_test_database

    with app.app_context():
        ensure_test_database()
        db.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    last_login_at TIMESTAMPTZ,
                    updated_at TIMESTAMPTZ
                );
                """
            )
        )
        db.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id VARCHAR(128) PRIMARY KEY,
                    admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    revoked_at TIMESTAMPTZ,
                    last_seen_at TIMESTAMPTZ
                );
                """
            )
        )
        db.session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS admin_login_attempts (
                    id SERIAL PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL,
                    username VARCHAR(80) NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 1,
                    blocked_until TIMESTAMPTZ,
                    last_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
        )
        db.session.commit()


def _register_create_admin_command(app: Flask) -> None:
    """Registra el comando seguro para crear el primer administrador."""

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True, help="Nombre de usuario del administrador.")
    def create_admin_cli(username: str):
        """Crea el primer administrador del sistema con validación segura."""
        try:
            with app.app_context():
                _ensure_target_database(app)

                if not db.inspect(db.engine).has_table("admins"):
                    raise RuntimeError(
                        "Las tablas de autenticación aún no existen; ejecuta la migración antes de crear el administrador."
                    )

                username = username.strip()
                if not username:
                    raise ValueError("El nombre de usuario es obligatorio.")

                password = click.prompt("Contraseña", hide_input=True, confirmation_prompt=True)
                _validate_admin_password(password)

                exists = db.session.execute(
                    select(Admin).where(Admin.username == username)
                ).scalar_one_or_none()
                if exists is not None:
                    raise ValueError("El nombre de usuario ya existe.")

                create_admin_account(username, password)
                click.echo(f"Administrador creado correctamente: {username}")
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        except Exception as exc:
            raise click.ClickException("No se pudo crear el administrador.") from exc


def create_app(config_class=Config):
    """
    Crea y configura una instancia de Flask.

    Args:
        config_class:
            Clase de configuración que utilizará la aplicación.
            Por defecto se utiliza Config.

    Returns:
        Flask:
            Instancia configurada de la aplicación.
    """

    app = Flask(__name__)
    app.config.from_object(config_class)

    # SECRET_KEY: validar para producción, generar para desarrollo
    if config_class.__name__ == "ProductionConfig":
        # Producción: requerir SECRET_KEY de entorno
        env_secret_key = os.getenv("SECRET_KEY")
        if not env_secret_key:
            raise RuntimeError(
                "SECRET_KEY no está configurado. "
                "Establezca la variable de entorno SECRET_KEY con un valor seguro aleatorio "
                "antes de iniciar la aplicación en producción."
            )
        app.config["SECRET_KEY"] = env_secret_key
    elif not app.config.get("SECRET_KEY"):
        # Desarrollo/pruebas: generar aleatorio
        app.config["SECRET_KEY"] = secrets.token_urlsafe(32)

    # Configuración de sesiones (si no está definida en config_class)
    if "SESSION_COOKIE_HTTPONLY" not in app.config:
        app.config["SESSION_COOKIE_HTTPONLY"] = True
    if "SESSION_COOKIE_SECURE" not in app.config:
        app.config["SESSION_COOKIE_SECURE"] = False
    if "SESSION_COOKIE_SAMESITE" not in app.config:
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if "PERMANENT_SESSION_LIFETIME" not in app.config:
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.before_request
    def protect_admin_routes():
        if request.path in {"/api/health", "/api/auth/csrf", "/api/auth/login", "/api/auth/logout", "/api/auth/session"}:
            return None
        if request.endpoint is None or request.path.startswith("/static"):
            return None

        try:
            require_admin_auth()
        except PermissionError:
            return jsonify({"error": "Autenticación requerida."}), 401
        except Exception:
            return jsonify({"error": "La sesión ha expirado o sido revocada."}), 401

                # Validar CSRF en operaciones de escritura autenticadas.
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            from app.services.admin_service import validate_csrf_token

            csrf_token = request.headers.get("X-CSRF-Token")

            if not csrf_token and request.is_json:
                data = request.get_json(silent=True)
                if isinstance(data, dict):
                    csrf_token = data.get("csrf_token")

            if not csrf_token and request.form:
                csrf_token = request.form.get("csrf_token")

            if not validate_csrf_token(csrf_token):
                return jsonify({
                    "error": "Token CSRF inválido o ausente."
                }), 403

    _ensure_auth_tables(app)
    _register_create_admin_command(app)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(admin_auth_bp, url_prefix="/api")
    app.register_blueprint(clients_bp, url_prefix="/api")
    app.register_blueprint(areas_bp, url_prefix="/api")
    app.register_blueprint(plans_bp, url_prefix="/api")
    app.register_blueprint(memberships_bp, url_prefix="/api")
    app.register_blueprint(payments_bp, url_prefix="/api")

    return app
