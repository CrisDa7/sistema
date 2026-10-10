"""Pruebas del servicio de clientes."""

import pytest

from app.models.client import Client
from app.services.client_service import prepare_client, ensure_cedula_available


def test_prepare_client_creates_valid_client():
    """Prepara un cliente con datos válidos."""

    client = prepare_client(
        cedula="0102030400",
        first_name="  María   Fernanda  ",
        last_name="Muñoz",
        phone="0991234567",
    )

    assert isinstance(client, Client)
    assert client.cedula == "0102030400"
    assert client.first_name == "María Fernanda"
    assert client.last_name == "Muñoz"
    assert client.phone == "0991234567"


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("cedula", "1234567890"),
        ("first_name", "Juan123"),
        ("last_name", ""),
        ("phone", "12345"),
    ],
)
def test_prepare_client_rejects_invalid_data(
    field,
    invalid_value,
):
    """Rechaza datos incorrectos antes de crear el cliente."""

    data = {
        "cedula": "0102030400",
        "first_name": "Juan",
        "last_name": "Pérez",
        "phone": "0991234567",
    }

    data[field] = invalid_value

    with pytest.raises(ValueError):
        prepare_client(**data)


def test_ensure_cedula_available_accepts_new_cedula():
    """Permite una cédula que todavía no existe."""

    existing_cedulas = {"1710034065"}

    result = ensure_cedula_available(
        "0102030400",
        existing_cedulas,
    )

    assert result is None


def test_ensure_cedula_available_rejects_duplicate():
    """Rechaza una cédula ya registrada."""

    existing_cedulas = {
        "0102030400",
        "1710034065",
    }

    with pytest.raises(
        ValueError,
        match="Ya existe un cliente",
    ):
        ensure_cedula_available(
            "0102030400",
            existing_cedulas,
        )


def test_ensure_cedula_available_rejects_invalid_cedula():
    """Rechaza una cédula inválida aunque no esté duplicada."""

    with pytest.raises(ValueError):
        ensure_cedula_available(
            "1234567890",
            set(),
        )