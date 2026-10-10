"""Servicios para el módulo de planes de Active Gym."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.area import Area
from app.models.plan import Plan
from app.validators.plan_validator import validate_plan_name, validate_plan_price


class PlanError(ValueError):
    """Error base del dominio de planes."""


class DuplicatePlanError(PlanError):
    """Se lanza cuando el nombre del plan ya existe."""


class PlanNotFoundError(PlanError):
    """Se lanza cuando el plan no existe."""


class AreaNotFoundForPlanError(PlanError):
    """Se lanza cuando una área asignada no existe."""


def register_plan(name: str, price: Decimal | str | int | float, area_ids: list[int] | None = None) -> Plan:
    """Registra un plan con sus áreas asociadas."""
    normalized_name = validate_plan_name(name)
    normalized_price = validate_plan_price(price)

    existing = db.session.execute(
        select(Plan).where(db.func.lower(Plan.name) == normalized_name.lower())
    ).scalar_one_or_none()
    if existing is not None:
        raise DuplicatePlanError("Ya existe un plan registrado con este nombre.")

    if area_ids is not None:
        if not area_ids:
            raise ValueError("Debe asignar al menos una área al plan.")
        if len(set(area_ids)) != len(area_ids):
            raise ValueError("No se pueden repetir áreas en un mismo plan.")

    plan = Plan(name=normalized_name, price=normalized_price)

    if area_ids:
        selected_areas = db.session.execute(
            select(Area).where(Area.id.in_(area_ids))
        ).scalars().all()
        if len(selected_areas) != len(set(area_ids)):
            raise AreaNotFoundForPlanError("Una o más áreas seleccionadas no existen.")
        plan.areas = selected_areas

    try:
        db.session.add(plan)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DuplicatePlanError("Ya existe un plan registrado con este nombre.") from exc

    return plan


def get_plan_by_id(plan_id: int) -> Plan | None:
    """Obtiene un plan por su identificador."""
    return db.session.get(Plan, plan_id)


def list_plans() -> list[Plan]:
    """Lista todos los planes en orden por ID."""
    return list(db.session.execute(select(Plan).order_by(Plan.id)).scalars().all())


def update_plan(plan_id: int, *, name: str | None = None, price: Decimal | str | int | float | None = None, area_ids: list[int] | None = None) -> Plan:
    """Actualiza datos del plan sin afectar historial de membresías."""
    plan = db.session.get(Plan, plan_id)
    if plan is None:
        raise PlanNotFoundError("El plan no existe.")

    if name is not None:
        normalized_name = validate_plan_name(name)
        if normalized_name.lower() != plan.name.lower():
            existing = db.session.execute(
                select(Plan).where(db.func.lower(Plan.name) == normalized_name.lower())
            ).scalar_one_or_none()
            if existing is not None and existing.id != plan.id:
                raise DuplicatePlanError("Ya existe un plan registrado con este nombre.")
        plan.name = normalized_name

    if price is not None:
        plan.price = validate_plan_price(price)

    if area_ids is not None:
        if not area_ids:
            raise ValueError("Debe asignar al menos una área al plan.")
        selected_areas = db.session.execute(
            select(Area).where(Area.id.in_(area_ids))
        ).scalars().all()
        if len(selected_areas) != len(set(area_ids)):
            raise AreaNotFoundForPlanError("Una o más áreas seleccionadas no existen.")
        plan.areas = selected_areas

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DuplicatePlanError("Ya existe un plan registrado con este nombre.") from exc

    return plan
