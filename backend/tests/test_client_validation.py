"""Pruebas de validación de datos de clientes."""

import pytest

from app.validators.client_validator import validate_person_name, validate_ecuadorian_cedula, validate_ecuadorian_phone


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Cristian", "Cristian"),
        ("José Luis", "José Luis"),
        ("María Fernanda", "María Fernanda"),
        ("Muñoz", "Muñoz"),
        ("De la Cruz", "De la Cruz"),
        ("  María   Fernanda  ", "María Fernanda"),
        ("Ana-María", "Ana-María"),
    ],
)
def test_validate_person_name_accepts_valid_names(
    name,
    expected,
):
    """Acepta nombres válidos y normaliza espacios."""

    assert validate_person_name(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "",
        "   ",
        "Cristian123",
        "12345",
        "Juan@",
        "Ana!",
        "A" * 101,
        None,
    ],
)
def test_validate_person_name_rejects_invalid_names(name):
    """Rechaza nombres vacíos o incorrectos."""

    with pytest.raises(ValueError):
        validate_person_name(name)


@pytest.mark.parametrize(
    "cedula",
    [
        "0102030400",
        "1710034065",
    ],
)
def test_validate_ecuadorian_cedula_accepts_valid(cedula):
    """Acepta cédulas con estructura y verificador correctos."""

    assert validate_ecuadorian_cedula(cedula) == cedula


@pytest.mark.parametrize(
    "cedula",
    [
        "",
        "123",
        "12345678901",
        "abcdefghij",
        "0102030401",
        "2502030400",
        "0162030400",
        "01020A0400",
        "010 030400",
        None,
    ],
)
def test_validate_ecuadorian_cedula_rejects_invalid(cedula):
    """Rechaza cédulas incorrectas."""

    with pytest.raises(ValueError):
        validate_ecuadorian_cedula(cedula)


@pytest.mark.parametrize(
    "phone",
    [
        "0991234567",
        "0987654321",
        "0961234567",
    ],
)
def test_validate_ecuadorian_phone_accepts_valid(phone):
    """Acepta celulares ecuatorianos válidos."""

    assert validate_ecuadorian_phone(phone) == phone


@pytest.mark.parametrize(
    "phone",
    [
        "",
        "991234567",
        "099123456",
        "09912345678",
        "099123ABCD",
        "022345678",
        "099 1234567",
        "+593991234567",
        None,
        991234567,
    ],
)
def test_validate_ecuadorian_phone_rejects_invalid(phone):
    """Rechaza celulares con formato incorrecto."""

    with pytest.raises(ValueError):
        validate_ecuadorian_phone(phone)