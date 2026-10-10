"""Modelos de administración de Active Gym."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Admin(db.Model):
    """Representa al administrador del sistema."""

    __tablename__ = "admins"
    __table_args__ = (
        UniqueConstraint("username", name="uq_admins_username"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    username: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sessions: Mapped[list["AdminSession"]] = relationship(
        "AdminSession",
        back_populates="admin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Admin id={self.id} username='{self.username}'>"


class AdminSession(db.Model):
    """Estado de sesión del administrador autenticado."""

    __tablename__ = "admin_sessions"

    id: Mapped[str] = mapped_column(
        String(128),
        primary_key=True,
    )

    admin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("admins.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    admin: Mapped[Admin] = relationship(
        "Admin",
        back_populates="sessions",
    )

    def __repr__(self) -> str:
        return f"<AdminSession id={self.id} admin_id={self.admin_id}>"


class AdminLoginAttempt(db.Model):
    """Registra intentos fallidos de login para mitigar fuerza bruta."""

    __tablename__ = "admin_login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    blocked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<AdminLoginAttempt ip={self.ip_address} "
            f"username='{self.username}' attempts={self.attempt_count}>"
        )
