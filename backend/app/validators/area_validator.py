"""Validaciones para nombres de áreas del gimnasio."""

import re


def validate_area_name(value: str) -> str:
    """Valida y normaliza el nombre de un área."""
    if not isinstance(value, str):
        raise ValueError("El nombre del área debe ser texto.")

    normalized_value = " ".join(value.split())
    if not normalized_value:
        raise ValueError("El nombre del área es obligatorio.")

    if len(normalized_value) > 100:
        raise ValueError("El nombre del área no puede superar los 100 caracteres.")

    if not re.fullmatch(
        r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ -][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*",
        normalized_value,
    ):
        raise ValueError(
            "El nombre del área solo puede contener letras, espacios y guiones."
        )

    return normalized_value
