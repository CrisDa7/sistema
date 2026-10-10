"""Servicios de autenticación para administradores de Active Gym."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from flask import request, session
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.admin import Admin, AdminLoginAttempt, AdminSession

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 900
SESSION_TIMEOUT_HOURS = 8


class AdminNotFoundError(ValueError):
    """Se lanza cuando no existe un administrador."""


class InvalidCredentialsError(ValueError):
    """Se lanza cuando las credenciales no validan."""


class BruteForceLockError(ValueError):
    """Se lanza cuando la IP/usuario está bloqueado."""


class AdminLimitReachedError(ValueError):
    """Se lanza cuando se intenta crear un segundo administrador en el MVP."""


class SessionExpiredError(ValueError):
    """Se lanza cuando la sesión ya expiró."""


class SessionRevokedError(ValueError):
    """Se lanza cuando la sesión fue revocada."""


class CSRFTokenError(ValueError):
    """Se lanza cuando el token CSRF no es válido."""


def _utc_now() -> datetime:
    """Devuelve un datetime UTC actual."""
    return datetime.now(timezone.utc)


def normalize_username(value: str) -> str:
    """Normaliza el nombre de usuario y valida que exista."""
    username = (value or "").strip()
    if not username:
        raise ValueError("El nombre de usuario es obligatorio.")
    return username


def get_client_ip() -> str:
    """Obtiene la IP del cliente para el control de fuerza bruta."""
    if request.access_route:
        return request.access_route[0]
    return request.remote_addr or "unknown"


def get_login_attempt(username: str, ip_address: str) -> AdminLoginAttempt | None:
    """Obtiene el último intento registrado para un usuario y una IP."""
    return db.session.execute(
        select(AdminLoginAttempt)
        .where(
            AdminLoginAttempt.username == username,
            AdminLoginAttempt.ip_address == ip_address,
        )
        .order_by(AdminLoginAttempt.last_attempt_at.desc())
    ).scalar()


def get_admin_by_username(username: str) -> Admin | None:
    """Obtiene un administrador por nombre de usuario."""
    normalized = normalize_username(username)
    return db.session.execute(
        select(Admin).where(Admin.username == normalized)
    ).scalar()


def create_admin_account(username: str, password: str) -> Admin:
    """Crea el primer administrador del sistema (MVP con un solo admin)."""
    normalized = normalize_username(username)
    if not password or not password.strip():
        raise ValueError("La contraseña es obligatoria.")

    total_admins = db.session.execute(select(db.func.count(Admin.id))).scalar_one() or 0
    if total_admins >= 1:
        raise AdminLimitReachedError(
            "El MVP solo permite un único administrador activo."
        )

    admin = Admin(
        username=normalized,
        password_hash=generate_password_hash(password),
        is_active=True,
        is_primary=True,
    )
    db.session.add(admin)
    db.session.commit()
    return admin


def _record_login_failure(username: str, ip_address: str) -> None:
    """Registra un intento fallido y aplica bloqueo si corresponde."""
    record = get_login_attempt(username, ip_address)
    now = _utc_now()

    if record is None:
        record = AdminLoginAttempt(
            ip_address=ip_address,
            username=username,
            attempt_count=1,
            last_attempt_at=now,
            created_at=now,
        )
        db.session.add(record)
        db.session.commit()
        return

    record.attempt_count += 1
    record.last_attempt_at = now

    if record.attempt_count >= MAX_LOGIN_ATTEMPTS:
        record.blocked_until = now + timedelta(seconds=LOCKOUT_SECONDS)

    db.session.commit()


def _clear_login_failures(username: str, ip_address: str) -> None:
    """Limpia los registros de bloqueo tras un login correcto."""
    attempts = db.session.execute(
        select(AdminLoginAttempt).where(
            AdminLoginAttempt.username == username,
            AdminLoginAttempt.ip_address == ip_address,
        )
    ).scalars().all()

    for attempt in attempts:
        db.session.delete(attempt)
    db.session.commit()


def is_login_blocked(username: str, ip_address: str) -> bool:
    """Comprueba si el usuario o la IP están bloqueados por fuerza bruta."""
    record = get_login_attempt(username, ip_address)
    if record is None:
        return False
    if record.blocked_until and record.blocked_until > _utc_now():
        return True
    return False


def authenticate_admin(username: str, password: str) -> Admin:
    """Valida un login y devuelve el administrador si es correcto."""
    normalized = normalize_username(username)
    ip_address = get_client_ip()

    if is_login_blocked(normalized, ip_address):
        raise BruteForceLockError(
            "Demasiados intentos fallidos. Inténtelo más tarde."
        )

    admin = get_admin_by_username(normalized)
    if admin is None or not admin.is_active:
        _record_login_failure(normalized, ip_address)
        raise InvalidCredentialsError("Credenciales inválidas.")

    if not check_password_hash(admin.password_hash, password):
        _record_login_failure(normalized, ip_address)
        raise InvalidCredentialsError("Credenciales inválidas.")

    _clear_login_failures(normalized, ip_address)
    admin.last_login_at = _utc_now()
    db.session.commit()
    return admin


def generate_csrf_token() -> str:
    """Genera un token CSRF para asegurar los formularios JSON."""
    return secrets.token_urlsafe(32)


def get_csrf_token() -> str | None:
    """Obtiene el token CSRF actual de la sesión."""
    return session.get("csrf_token")


def validate_csrf_token(token: str | None) -> bool:
    """Valida que el token CSRF recibido coincida con el de la sesión."""
    expected = get_csrf_token()
    if expected is None:
        return False
    return bool(token) and token == expected


def issue_session_for_admin(admin: Admin) -> str:
    """Crea una sesión autenticada en PostgreSQL con expiración de 8 horas."""
    session_id = secrets.token_urlsafe(32)
    expires_at = _utc_now() + timedelta(hours=SESSION_TIMEOUT_HOURS)
    now = _utc_now()

    db.session.execute(
        AdminSession.__table__.delete().where(AdminSession.admin_id == admin.id)
    )

    row = AdminSession(
        id=session_id,
        admin_id=admin.id,
        created_at=now,
        expires_at=expires_at,
        revoked_at=None,
        last_seen_at=now,
    )
    db.session.add(row)
    db.session.commit()
    return session_id


def revoke_current_session() -> None:
    """Revoca la sesión autenticada y elimina la cookie de Flask."""
    session_id = session.get("session_id")
    if not session_id:
        return

    existing = db.session.get(AdminSession, session_id)
    if existing is not None and existing.revoked_at is None:
        existing.revoked_at = _utc_now()
        db.session.commit()

    session.clear()


def get_current_admin() -> Admin | None:
    """Obtiene el administrador autenticado si la sesión es válida."""
    session_id = session.get("session_id")
    if not session_id:
        return None

    session_row = db.session.get(AdminSession, session_id)
    if session_row is None:
        session.clear()
        return None

    if session_row.revoked_at is not None:
        raise SessionRevokedError("La sesión ha sido revocada.")

    now_utc = _utc_now()
    if session_row.expires_at <= now_utc:
        session_row.revoked_at = now_utc
        db.session.commit()
        session.clear()
        raise SessionExpiredError("La sesión ha expirado.")

    admin = db.session.get(Admin, session_row.admin_id)
    if admin is None or not admin.is_active:
        session.clear()
        return None

    session_row.last_seen_at = now_utc
    db.session.commit()
    return admin


def require_admin_auth() -> Admin:
    """Valida que exista una sesión activa y devuelve el administrador."""
    admin = get_current_admin()
    if admin is None:
        raise PermissionError("Autenticación requerida.")
    return admin
