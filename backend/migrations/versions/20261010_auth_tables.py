"""Create admin auth tables.

Revision ID: 20261010_auth_tables
Revises:
Create Date: 2026-10-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20261010_auth_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("username", name="uq_admins_username"),
    )
    op.create_index(op.f("ix_admins_username"), "admins", ["username"], unique=True)

    op.create_table(
        "admin_sessions",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["admin_id"], ["admins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_sessions_admin_id"), "admin_sessions", ["admin_id"], unique=False)

    op.create_table(
        "admin_login_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index(op.f("ix_admin_login_attempts_ip_address"), "admin_login_attempts", ["ip_address"], unique=False)
    op.create_index(op.f("ix_admin_login_attempts_username"), "admin_login_attempts", ["username"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_login_attempts_username"), table_name="admin_login_attempts")
    op.drop_index(op.f("ix_admin_login_attempts_ip_address"), table_name="admin_login_attempts")
    op.drop_table("admin_login_attempts")
    op.drop_index(op.f("ix_admin_sessions_admin_id"), table_name="admin_sessions")
    op.drop_table("admin_sessions")
    op.drop_index(op.f("ix_admins_username"), table_name="admins")
    op.drop_table("admins")
