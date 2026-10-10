"""create_business_tables

Revision ID: 3868a9c6d1c9
Revises: 20261010_auth_tables
Create Date: 2026-10-10 12:11:15.628250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3868a9c6d1c9'
down_revision = '20261010_auth_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tabla: clients
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cedula", sa.String(length=10), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("registration_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cedula", name="uq_clients_cedula"),
    )
    op.create_index(op.f("ix_clients_cedula"), "clients", ["cedula"], unique=True)

    # Tabla: areas
    op.create_table(
        "areas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_areas_name"),
    )

    # Tabla: plans
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_plans_name"),
    )

    # Tabla intermedia: plan_areas
    op.create_table(
        "plan_areas",
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ),
        sa.PrimaryKeyConstraint("plan_id", "area_id"),
    )

    # Tabla: memberships
    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("contracted_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Tabla intermedia: membership_areas
    op.create_table(
        "membership_areas",
        sa.Column("membership_id", sa.Integer(), nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["area_id"], ["areas.id"], ),
        sa.ForeignKeyConstraint(["membership_id"], ["memberships.id"], ),
        sa.PrimaryKeyConstraint("membership_id", "area_id"),
    )

    # Tabla: payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("membership_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("transfer_reference", sa.String(length=100), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        sa.ForeignKeyConstraint(["membership_id"], ["memberships.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("membership_id", name="uq_payments_membership_id"),
    )
    op.create_index(op.f("ix_payments_membership_id"), "payments", ["membership_id"], unique=True)
    op.create_index(
        op.f("ix_payments_transfer_reference_unique"),
        "payments",
        ["transfer_reference"],
        unique=True,
        postgresql_where=sa.text("transfer_reference IS NOT NULL")
    )


def downgrade() -> None:
    # Eliminar en orden inverso por dependencias de FK
    op.drop_index(op.f("ix_payments_transfer_reference_unique"), table_name="payments")
    op.drop_index(op.f("ix_payments_membership_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_table("membership_areas")
    op.drop_table("memberships")
    op.drop_table("plan_areas")
    op.drop_table("plans")
    op.drop_index(op.f("ix_clients_cedula"), table_name="clients")
    op.drop_table("clients")
    op.drop_table("areas")
