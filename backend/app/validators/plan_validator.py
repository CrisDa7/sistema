"""Validaciones para nombres y precios de planes."""

from decimal import Decimal, InvalidOperation

from app.validators.area_validator import validate_area_name


def validate_plan_name(value: str) -> str:
    """Valida y normaliza el nombre de un plan."""
    if not isinstance(value, str):
        raise ValueError("El nombre del plan debe ser texto.")

    normalized_value = " ".join(value.split())
    if not normalized_value:
        raise ValueError("El nombre del plan es obligatorio.")

    if len(normalized_value) > 150:
        raise ValueError("El nombre del plan no puede superar los 150 caracteres.")

    return normalized_value


def validate_plan_price(value: object) -> Decimal:
    """Valida que el precio del plan sea un valor monetario válido."""
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, (int, float, str)):
        try:
            decimal_value = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError("El precio del plan debe ser un número válido.") from exc
    else:
        raise ValueError("El precio del plan debe ser un número válido.")

    if decimal_value <= 0:
        raise ValueError("El precio del plan debe ser mayor a cero.")

    return decimal_value.quantize(Decimal("0.01"))


def validate_area_list(area_names: list[str]) -> list[str]:
    """Valida una lista de nombres de área y normaliza cada uno."""
    if not isinstance(area_names, list):
        raise ValueError("Debe enviar una lista de áreas válidas.")

    if not area_names:
        raise ValueError("Debe asignar al menos una área al plan.")

    normalized = []
    for area_name in area_names:
        normalized.append(validate_area_name(area_name))

    return normalized
