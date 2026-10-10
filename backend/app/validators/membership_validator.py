"""Validaciones del dominio de membresías."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation


def validate_membership_dates(start_date: date, end_date: date) -> tuple[date, date]:
    """Valida fechas de inicio y fin de una membresía."""
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise ValueError("Las fechas de la membresía deben ser válidas.")

    if start_date > end_date:
        raise ValueError("La fecha de inicio no puede ser posterior a la de fin.")

    return start_date, end_date


def validate_area_ids(area_ids: list[int] | tuple[int, ...] | set[int] | None) -> list[int]:
    """Normaliza y valida una lista de áreas asignadas a la membresía."""
    if area_ids is None:
        raise ValueError("Debe seleccionar al menos un área para la membresía.")

    if isinstance(area_ids, (str, bytes)):
        raise ValueError("Las áreas deben enviarse como una lista de identificadores.")

    normalized = []
    seen = set()
    for area_id in area_ids:
        if not isinstance(area_id, int):
            raise ValueError("Cada área debe tener un identificador numérico válido.")
        if area_id in seen:
            continue
        seen.add(area_id)
        normalized.append(area_id)

    if not normalized:
        raise ValueError("Debe seleccionar al menos un área para la membresía.")

    return normalized


def validate_contracted_price(value: object) -> Decimal:
    """Valida el precio contratado para la membresía."""
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, (int, float, str)):
        try:
            decimal_value = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError("El precio contratado debe ser un número válido.") from exc
    else:
        raise ValueError("El precio contratado debe ser un número válido.")

    if decimal_value <= 0:
        raise ValueError("El precio contratado debe ser mayor a cero.")

    return decimal_value.quantize(Decimal("0.01"))
