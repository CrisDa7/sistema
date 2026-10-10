"""Servicios para la gestión de membresías."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.area import Area
from app.models.client import Client
from app.models.membership import Membership, membership_areas
from app.models.plan import Plan
from app.services.membership_dates import calculate_expiration_date, calculate_renewal_start_date
from app.services.membership_validation import has_membership_conflict
from app.validators.membership_validator import (
    validate_area_ids,
    validate_contracted_price,
    validate_membership_dates,
)


class MembershipError(ValueError):
    """Error base del dominio de membresías."""


class MembershipNotFoundError(MembershipError):
    """Se lanza cuando una membresía no existe."""


class ClientNotFoundForMembershipError(MembershipError):
    """Se lanza cuando el cliente asociado no existe."""


class PlanNotFoundForMembershipError(MembershipError):
    """Se lanza cuando el plan asociado no existe."""


class AreaNotFoundForMembershipError(MembershipError):
    """Se lanza cuando una o más áreas asociadas no existen."""


class MembershipConflictError(MembershipError):
    """Se lanza cuando la nueva membresía entra en conflicto."""


def _get_area_objects(area_ids: list[int]) -> list[Area]:
    """Carga las áreas seleccionadas y valida que existan."""
    if not area_ids:
        raise AreaNotFoundForMembershipError("Debe seleccionar al menos un área para la membresía.")

    selected = db.session.execute(select(Area).where(Area.id.in_(area_ids))).scalars().all()
    if len(selected) != len(set(area_ids)):
        missing_ids = sorted(set(area_ids) - {area.id for area in selected})
        raise AreaNotFoundForMembershipError(
            "Una o más áreas seleccionadas no existen: " + ", ".join(map(str, missing_ids)) + "."
        )

    return selected


def get_membership_by_id(membership_id: int) -> Membership | None:
    """Devuelve una membresía por su identificador."""
    return db.session.get(Membership, membership_id)


def list_memberships() -> list[Membership]:
    """Lista todas las membresías ordenadas por ID."""
    return list(db.session.execute(select(Membership).order_by(Membership.id)).scalars().all())


def list_memberships_by_client(client_id: int) -> list[Membership]:
    """Lista las membresías de un cliente ordenadas por fecha de inicio."""
    return list(
        db.session.execute(
            select(Membership)
            .where(Membership.client_id == client_id)
            .order_by(Membership.start_date.desc(), Membership.id.desc())
        ).scalars().all()
    )


def calculate_membership_status(membership: Membership) -> str:
    """Calcula el estado dinámico de una membresía según sus fechas."""
    today = date.today()

    if today < membership.start_date:
        return "pendiente"
    if today <= membership.end_date:
        return "vigente"
    return "vencida"


def calculate_reminder_date(membership: Membership) -> date:
    """La fecha de recordatorio es end_date, según la regla de negocio."""
    return membership.end_date


def register_membership(
    client_id: int,
    plan_id: int,
    start_date: date,
    end_date: date,
    area_ids: list[int] | tuple[int, ...] | set[int],
    contracted_price: Decimal | int | float | str | None = None,
    skip_conflict_validation: bool = False,
) -> Membership:
    """Registra una membresía válida para un cliente y plan."""
    if not isinstance(client_id, int):
        raise ClientNotFoundForMembershipError("El cliente es obligatorio.")
    if not isinstance(plan_id, int):
        raise PlanNotFoundForMembershipError("El plan es obligatorio.")

    client = db.session.get(Client, client_id)
    if client is None:
        raise ClientNotFoundForMembershipError("El cliente no existe.")

    plan = db.session.get(Plan, plan_id)
    if plan is None:
        raise PlanNotFoundForMembershipError("El plan no existe.")

    normalized_area_ids = validate_area_ids(area_ids)
    selected_areas = _get_area_objects(normalized_area_ids)

    start_date, end_date = validate_membership_dates(start_date, end_date)

    if contracted_price is None:
        effective_price = Decimal(str(plan.price))
    else:
        effective_price = validate_contracted_price(contracted_price)

    if not skip_conflict_validation:
        existing_memberships = list_memberships_by_client(client_id)
        if has_membership_conflict(
            existing_memberships=existing_memberships,
            new_start=start_date,
            new_end=end_date,
            new_area_ids=set(normalized_area_ids),
        ):
            raise MembershipConflictError("La membresía entra en conflicto con otra vigencia del cliente.")

    membership = Membership(
        client_id=client.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        contracted_price=effective_price,
        areas=selected_areas,
    )

    try:
        db.session.add(membership)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise MembershipConflictError("No se pudo registrar la membresía por un conflicto de integridad.") from exc

    return membership


def get_membership_period_end(start_date: date) -> date:
    """Devuelve el último día pagado del período mensual."""
    return calculate_expiration_date(start_date)


def renew_membership_continuity(
    membership_id: int,
    renewal_date: date | None = None,
    area_ids: list[int] | tuple[int, ...] | set[int] | None = None,
    contracted_price: Decimal | int | float | str | None = None,
) -> Membership:
    """Renueva una membresía por continuidad: siempre inicia en el día siguiente al último día pagado."""
    membership = db.session.get(Membership, membership_id)
    if membership is None:
        raise MembershipNotFoundError("La membresía no existe.")

    if renewal_date is not None and not isinstance(renewal_date, date):
        raise ValueError("La fecha de renovación debe ser una fecha válida.")

    # Regla definitiva: continuidad = siguiente día del último período pagado.
    next_start = membership.end_date + timedelta(days=1)
    next_end = calculate_expiration_date(next_start)

    normalized_area_ids = validate_area_ids(area_ids if area_ids is not None else [area.id for area in membership.areas])
    selected_areas = _get_area_objects(normalized_area_ids)
    effective_price = validate_contracted_price(contracted_price) if contracted_price is not None else membership.contracted_price

    return register_membership(
        client_id=membership.client_id,
        plan_id=membership.plan_id,
        start_date=next_start,
        end_date=next_end,
        area_ids=normalized_area_ids,
        contracted_price=effective_price,
    )


def register_reentry_membership(
    client_id: int,
    plan_id: int,
    start_date: date,
    end_date: date | None = None,
    area_ids: list[int] | tuple[int, ...] | set[int] | None = None,
    contracted_price: Decimal | int | float | str | None = None,
    previous_membership_id: int | None = None,
) -> Membership:
    """Registra un reingreso tras ausencia usando la fecha real de regreso como inicio."""
    if not isinstance(start_date, date):
        raise ValueError("La fecha de reingreso es obligatoria.")

    if end_date is None:
        end_date = calculate_expiration_date(start_date)

    if previous_membership_id is not None:
        previous_membership = db.session.get(Membership, previous_membership_id)
        if previous_membership is None:
            raise MembershipNotFoundError("La membresía anterior no existe.")
        if area_ids is None:
            area_ids = [area.id for area in previous_membership.areas]
        if contracted_price is None:
            effective_price = previous_membership.contracted_price
        else:
            effective_price = validate_contracted_price(contracted_price)
    else:
        if area_ids is None:
            raise ValueError("Debe indicar áreas para el reingreso o proporcionar la membresía anterior.")
        if contracted_price is None:
            raise ValueError("Debe indicar el precio contratado para el reingreso o proporcionar la membresía anterior.")
        effective_price = validate_contracted_price(contracted_price)

    return register_membership(
        client_id=client_id,
        plan_id=plan_id,
        start_date=start_date,
        end_date=end_date,
        area_ids=area_ids,
        contracted_price=effective_price,
    )
