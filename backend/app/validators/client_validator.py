"""Validaciones de los datos de clientes de Active Gym."""

import re


def validate_person_name(value: str) -> str:
    """
    Valida y normaliza nombres y apellidos.

    Devuelve el nombre sin espacios innecesarios.

    Lanza ValueError cuando el nombre no es válido.
    """

    if not isinstance(value, str):
        raise ValueError("El nombre debe ser un texto.")

    normalized_name = " ".join(value.split())

    if not normalized_name:
        raise ValueError("El nombre es obligatorio.")

    if len(normalized_name) > 100:
        raise ValueError(
            "El nombre no puede superar los 100 caracteres."
        )

    if not re.fullmatch(
        r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+"
        r"(?:[ '-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*",
        normalized_name,
    ):
        raise ValueError(
            "El nombre solo puede contener letras, "
            "espacios, apóstrofes y guiones."
        )

    return normalized_name

def validate_ecuadorian_cedula(value: str) -> str:
    """
    Valida una cédula ecuatoriana de persona natural.

    Devuelve la cédula si es válida.
    Lanza ValueError si no cumple las reglas.
    """

    if not isinstance(value, str):
        raise ValueError("La cédula debe ser un texto.")

    if len(value) != 10 or not value.isascii() or not value.isdigit():
        raise ValueError("La cédula debe tener exactamente 10 dígitos.")

    province = int(value[:2])

    if not 1 <= province <= 24:
        raise ValueError("El código de provincia no es válido.")

    if int(value[2]) >= 6:
        raise ValueError("El tercer dígito de la cédula no es válido.")

    coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]

    total = 0

    for digit, coefficient in zip(value[:9], coefficients):
        result = int(digit) * coefficient

        if result >= 10:
            result -= 9

        total += result

    expected_check_digit = (10 - total % 10) % 10

    if int(value[9]) != expected_check_digit:
        raise ValueError("El dígito verificador de la cédula es incorrecto.")

    return value

def validate_ecuadorian_phone(value: str) -> str:
    """
    Valida un número celular ecuatoriano.

    Debe tener 10 dígitos y comenzar con 09.
    Devuelve el número validado.
    """

    if not isinstance(value, str):
        raise ValueError("El celular debe ser un texto.")

    if (
        len(value) != 10
        or not value.isascii()
        or not value.isdigit()
        or not value.startswith("09")
    ):
        raise ValueError(
            "El celular debe tener 10 dígitos y comenzar con 09."
        )

    return value