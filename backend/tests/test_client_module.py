"""Pruebas del módulo de clientes: servicio y API REST."""

from itertools import count

import pytest
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models.client import Client
from app.services.client_service import (
    get_client_by_id,
    list_clients,
    register_client,
    search_clients,
    update_client,
)
from app.validators.client_validator import (
    validate_ecuadorian_cedula,
    validate_ecuadorian_phone,
    validate_person_name,
)
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig
from tests.test_helpers import generate_valid_cedula


@pytest.fixture
def app():
    """Crea la aplicación configurada para la base de pruebas."""
    app = create_app(TestConfig)
    with app.app_context():
        ensure_test_database()
        db.session.execute(db.delete(Client))
        db.session.commit()
        yield app

    with app.app_context():
        ensure_test_database()
        db.session.execute(db.delete(Client))
        db.session.commit()


@pytest.fixture
def make_payload():
    """Genera payloads únicos para pruebas de escritura."""
    created = []
    counter = count(1000)

    def _factory(prefix: str = "cliente"):
        seed = next(counter)
        cedula = generate_valid_cedula(seed)
        while cedula in created:
            seed = next(counter)
            cedula = generate_valid_cedula(seed)

        payload = {
            "cedula": cedula,
            "first_name": f"{prefix} Uno",
            "last_name": "Pérez",
            "phone": "099" + str(1000000 + seed).rjust(7, "0")[:7],
        }
        created.append(payload["cedula"])
        return payload

    yield _factory

    with create_app(TestConfig).app_context():
        ensure_test_database()
        for cedula in created:
            db.session.execute(
                db.delete(Client).where(Client.cedula == cedula)
            )
        db.session.commit()


def test_register_client_success(app, make_payload):
    """Registra un cliente con datos válidos."""
    payload = make_payload("Ana")

    with app.app_context():
        client = register_client(
            cedula=payload["cedula"],
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            phone=payload["phone"],
        )

        assert client.id is not None
        assert client.cedula == payload["cedula"]
        assert client.first_name == "Ana Uno"
        assert client.last_name == "Pérez"
        assert client.phone == payload["phone"]
        assert client.registration_date is not None


def test_prepare_client_normalizes_names():
    """Normaliza espacios en nombres y apellidos."""
    app = create_app(TestConfig)

    with app.app_context():
        ensure_test_database()
        client = register_client(
            cedula=generate_valid_cedula(1001),
            first_name="  María   Fernanda  ",
            last_name="  De la   Cruz  ",
            phone="0991234567",
        )

        assert client.first_name == "María Fernanda"
        assert client.last_name == "De la Cruz"


def test_duplicate_cedula_is_rejected(app, make_payload):
    """Rechaza dos clientes con la misma cédula."""
    payload = make_payload("Clon")

    with app.app_context():
        register_client(**payload)

        with pytest.raises(ValueError, match="Ya existe un cliente registrado con esta cédula"):
            register_client(**payload)


def test_invalid_cedula_is_rejected():
    """Rechaza una cédula ecuatoriana inválida."""
    with pytest.raises(ValueError):
        validate_ecuadorian_cedula("1234567890")


def test_invalid_phone_is_rejected():
    """Rechaza un celular con formato incorrecto."""
    with pytest.raises(ValueError):
        validate_ecuadorian_phone("022345678")


def test_invalid_name_is_rejected():
    """Rechaza nombres con números o símbolos invalidos."""
    with pytest.raises(ValueError):
        validate_person_name("Juan123")


def test_get_client_by_id_returns_client(app, make_payload):
    """Consulta un cliente por su identificador."""
    payload = make_payload("Consulta")

    with app.app_context():
        created = register_client(**payload)
        fetched = get_client_by_id(created.id)

        assert fetched is not None
        assert fetched.cedula == payload["cedula"]


def test_get_client_by_id_not_found(app):
    """Devuelve None cuando el cliente no existe."""
    with app.app_context():
        assert get_client_by_id(999999) is None


def test_list_clients_returns_registered_clients(app, make_payload):
    """Lista clientes registrados ordenados por identificador."""
    payload_one = make_payload("Lista")
    payload_two = make_payload("Lista")

    with app.app_context():
        register_client(**payload_one)
        register_client(**payload_two)
        clients = list_clients()

        assert len(clients) >= 2
        assert any(client.cedula == payload_one["cedula"] for client in clients)
        assert any(client.cedula == payload_two["cedula"] for client in clients)


def test_search_clients_filters_by_name_or_cedula(app, make_payload):
    """Busca clientes por nombre, apellido o cédula."""
    payload = make_payload("Busqueda")

    with app.app_context():
        register_client(**payload)
        results = search_clients("Busqueda")

        assert any(client.cedula == payload["cedula"] for client in results)


def test_update_client_success(app, make_payload):
    """Actualiza nombres y teléfono de un cliente existente."""
    payload = make_payload("Actualiza")

    with app.app_context():
        created = register_client(**payload)
        updated = update_client(
            created.id,
            first_name="María José",
            last_name="Vargas",
            phone="0987654321",
        )

        assert updated.first_name == "María José"
        assert updated.last_name == "Vargas"
        assert updated.phone == "0987654321"


def test_update_client_rejects_invalid_data(app, make_payload):
    """Rechaza datos inválidos durante la actualización."""
    payload = make_payload("Invalido")

    with app.app_context():
        created = register_client(**payload)

        with pytest.raises(ValueError):
            update_client(created.id, first_name="Juan123")

        with pytest.raises(ValueError):
            update_client(created.id, phone="022345678")


def test_update_client_protects_readonly_fields(app, make_payload):
    """Bloquea cambios en ID, cédula y fecha de registro."""
    payload = make_payload("Protegido")

    with app.app_context():
        created = register_client(**payload)

        with pytest.raises(ValueError):
            update_client(created.id, cedula="0102030400")

        with pytest.raises(ValueError):
            update_client(created.id, id=999)

        with pytest.raises(ValueError):
            update_client(created.id, registration_date="2024-01-01")


def test_clients_can_share_name_and_phone(app, make_payload):
    """Permite clientes distintos con igual nombre o teléfono."""
    first_payload = make_payload("Compartido")
    second_payload = {
        "cedula": generate_valid_cedula(2000),
        "first_name": "Compartido Uno",
        "last_name": "García",
        "phone": first_payload["phone"],
    }

    with app.app_context():
        first_client = register_client(**first_payload)
        second_client = register_client(**second_payload)

        assert first_client.first_name == second_client.first_name
        assert first_client.phone == second_client.phone
        assert first_client.cedula != second_client.cedula


def test_client_api_create_and_fetch(app, make_payload, authenticated_client):
    """Prueba el flujo REST de creación y consulta por ID."""
    payload = make_payload("API")
    client = authenticated_client

    with app.app_context():
        response = client.post("/api/clients", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["cedula"] == payload["cedula"]

        created_id = data["id"]
        get_response = client.get(f"/api/clients/{created_id}")
        assert get_response.status_code == 200
        assert get_response.get_json()["cedula"] == payload["cedula"]


def test_client_api_invalid_data_and_not_found(app, authenticated_client):
    """Valida código HTTP 400 y 404 en la API REST."""
    client = authenticated_client

    invalid_response = client.post(
        "/api/clients",
        json={
            "cedula": "1234567890",
            "first_name": "Juan",
            "last_name": "Pérez",
            "phone": "0991234567",
        },
    )
    assert invalid_response.status_code == 400

    missing_response = client.get("/api/clients/999999")
    assert missing_response.status_code == 404


def test_client_api_patch_and_search(app, make_payload, authenticated_client):
    """Prueba búsqueda y actualización vía API REST."""
    payload = make_payload("Patch")
    client = authenticated_client

    with app.app_context():
        created_response = client.post("/api/clients", json=payload)
        created_id = created_response.get_json()["id"]

        patch_response = client.patch(
            f"/api/clients/{created_id}",
            json={"first_name": "Patricia Ana", "phone": "0987654321"},
        )
        assert patch_response.status_code == 200
        assert patch_response.get_json()["first_name"] == "Patricia Ana"

        list_response = client.get("/api/clients?search=Patricia")
        assert list_response.status_code == 200
        data = list_response.get_json()
        assert any(item["id"] == created_id for item in data)


def test_client_api_rejects_empty_or_invalid_json(app, authenticated_client):
    """Rechaza cuerpos JSON vacíos o de tipo incorrecto."""
    client = authenticated_client

    empty_response = client.post("/api/clients", json={})
    assert empty_response.status_code == 400

    invalid_response = client.post("/api/clients", data="not-json")
    assert invalid_response.status_code == 400


def test_client_api_duplicate_cedula_http_409(app, make_payload, authenticated_client):
    """Devuelve 409 cuando la cédula ya existe."""
    payload = make_payload("Duplicado")
    client = authenticated_client

    with app.app_context():
        first_response = client.post("/api/clients", json=payload)
        assert first_response.status_code == 201

        duplicate_response = client.post("/api/clients", json=payload)
        assert duplicate_response.status_code == 409
        assert "Ya existe un cliente registrado con esta cédula." in duplicate_response.get_json()["error"]


def test_client_api_patch_rejects_protected_fields(app, make_payload, authenticated_client):
    """No permite modificar campos protegidos mediante la API."""
    payload = make_payload("Protegido")
    client = authenticated_client

    with app.app_context():
        created = client.post("/api/clients", json=payload)
        client_id = created.get_json()["id"]

        protected_response = client.patch(
            f"/api/clients/{client_id}",
            json={"cedula": "0102030400"},
        )
        assert protected_response.status_code == 400


def test_client_api_patch_not_found(app, authenticated_client):
    """Devuelve 404 al intentar actualizar un cliente inexistente."""
    client = authenticated_client

    response = client.patch(
        "/api/clients/999999",
        json={"first_name": "Ana"},
    )
    assert response.status_code == 404


def test_client_api_post_invalid_fields_http_400(app, authenticated_client):
    """Valida códigos HTTP 400 para datos de entrada inválidos."""
    client = authenticated_client

    response = client.post(
        "/api/clients",
        json={
            "cedula": "1234567890",
            "first_name": "Juan123",
            "last_name": "Pérez",
            "phone": "022345678",
        },
    )
    assert response.status_code == 400


def test_client_api_patch_invalid_payload_type(app, make_payload, authenticated_client):
    """Rechaza payloads de tipo no soportado en PATCH."""
    payload = make_payload("Tipo")
    client = authenticated_client

    with app.app_context():
        created = client.post("/api/clients", json=payload)
        client_id = created.get_json()["id"]

        response = client.patch(
            f"/api/clients/{client_id}",
            data="[]",
        )
        assert response.status_code == 400
