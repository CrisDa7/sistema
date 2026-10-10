"""Pruebas del módulo de áreas."""

import uuid

import pytest

from app import create_app
from app.extensions import db
from app.models.area import Area
from app.models.plan import plan_areas
from app.services.area_service import (
    AreaNotFoundError,
    DuplicateAreaError,
    get_area_by_id,
    list_areas,
    register_area,
    update_area,
)
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig


def _unique_name(prefix: str) -> str:
    """Genera un nombre único por prueba sin depender de nombres fijos."""
    suffix = "".join(ch for ch in uuid.uuid4().hex if ch.isalpha())[:8]
    return f"{prefix} {suffix}"


def _delete_exact_area_ids(area_ids):
    """Elimina solo los IDs exactos pasados, sin tocar registros previos."""
    if not area_ids:
        return

    ids = list(area_ids)
    db.session.execute(db.delete(plan_areas).where(plan_areas.c.area_id.in_(ids)))
    db.session.execute(db.delete(Area).where(Area.id.in_(ids)))
    db.session.commit()


@pytest.fixture
def app():
    """App configurada para pruebas con aislamiento en active_gym_test_db."""
    app = create_app(TestConfig)
    with app.app_context():
        ensure_test_database()
        yield app


@pytest.fixture
def tracked_area_ids(app):
    """Registra los IDs creados por cada prueba y los elimina al final."""
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_area_ids(created_ids)


def test_register_area_success(app, tracked_area_ids):
    """Registra un área válida."""
    with app.app_context():
        area = register_area(_unique_name("Area Success"))
        tracked_area_ids.add(area.id)
        assert area.id is not None
        assert area.name.startswith("Area Success")


def test_register_area_rejects_invalid_name(app):
    """Rechaza un nombre vacío o inválido."""
    with app.app_context():
        with pytest.raises(ValueError):
            register_area("")
        with pytest.raises(ValueError):
            register_area("Musculación123")


def test_register_area_rejects_duplicate_name(app, tracked_area_ids):
    """Rechaza nombres duplicados sin distinguir mayúsculas."""
    with app.app_context():
        first = register_area(_unique_name("Area Dup"))
        tracked_area_ids.add(first.id)
        with pytest.raises(DuplicateAreaError):
            register_area(first.name.upper())


def test_list_areas(app, tracked_area_ids):
    """Lista áreas registradas."""
    with app.app_context():
        first = register_area(_unique_name("Area List A"))
        second = register_area(_unique_name("Area List B"))
        tracked_area_ids.update({first.id, second.id})
        areas = list_areas()
        assert len(areas) >= 2


def test_get_area_by_id(app, tracked_area_ids):
    """Consulta un área por ID."""
    with app.app_context():
        created = register_area(_unique_name("Area Get"))
        tracked_area_ids.add(created.id)
        fetched = get_area_by_id(created.id)
        assert fetched is not None
        assert fetched.name == created.name


def test_get_area_by_id_not_found(app):
    """Devuelve None si el área no existe."""
    with app.app_context():
        assert get_area_by_id(99999) is None


def test_update_area_success(app, tracked_area_ids):
    """Actualiza el nombre de un área."""
    with app.app_context():
        created = register_area(_unique_name("Area Update"))
        tracked_area_ids.add(created.id)
        original_name = created.name
        updated = update_area(created.id, name=f"{original_name} updated")
        assert updated.name == f"{original_name} updated"


def test_update_area_rejects_duplicate_name(app, tracked_area_ids):
    """Rechaza una duplicación de nombre durante la actualización."""
    with app.app_context():
        first = register_area(_unique_name("Area Dup Uno"))
        second = register_area(_unique_name("Area Dup Dos"))
        tracked_area_ids.update({first.id, second.id})
        with pytest.raises(DuplicateAreaError):
            update_area(second.id, name=first.name)


def test_area_api_endpoints(app, tracked_area_ids, authenticated_client):
    """Prueba creación, listado, consulta y actualización por HTTP."""
    client = authenticated_client
    name = _unique_name("Area API")
    updated_name = _unique_name("Area API Updated")

    with app.app_context():
        response = client.post("/api/areas", json={"name": name})
        assert response.status_code == 201
        payload = response.get_json()
        area_id = payload["id"]
        tracked_area_ids.add(area_id)

        list_response = client.get("/api/areas")
        assert list_response.status_code == 200
        assert any(item["id"] == area_id for item in list_response.get_json())

        get_response = client.get(f"/api/areas/{area_id}")
        assert get_response.status_code == 200
        assert get_response.get_json()["name"] == name

        patch_response = client.patch(f"/api/areas/{area_id}", json={"name": updated_name})
        assert patch_response.status_code == 200
        assert patch_response.get_json()["name"] == updated_name


def test_area_api_http_errors(app, tracked_area_ids, authenticated_client):
    """Valida 400, 404 y 409 para el módulo de áreas."""
    client = authenticated_client
    duplicate_name = _unique_name("Area HTTP Dup")

    invalid_response = client.post("/api/areas", json={"name": "123"})
    assert invalid_response.status_code == 400

    duplicate_response = client.post("/api/areas", json={"name": duplicate_name})
    assert duplicate_response.status_code == 201
    tracked_area_ids.add(duplicate_response.get_json()["id"])
    duplicate_again = client.post("/api/areas", json={"name": duplicate_name.upper()})
    assert duplicate_again.status_code == 409

    missing_response = client.get("/api/areas/999999")
    assert missing_response.status_code == 404


def test_cleanup_does_not_delete_preexisting_area(app, tracked_area_ids):
    """La limpieza no elimina un registro previo con un nombre habitual."""
    with app.app_context():
        suffix = "".join(ch for ch in uuid.uuid4().hex if ch.isalpha())[:8]
        existing = Area(name=f"Musculación Base {suffix}")
        db.session.add(existing)
        db.session.commit()

        created = register_area(_unique_name("Area Isolation"))
        tracked_area_ids.add(created.id)

        assert db.session.get(Area, existing.id) is not None
        assert db.session.get(Area, created.id) is not None

        _delete_exact_area_ids({created.id})

        assert db.session.get(Area, existing.id) is not None
        assert db.session.get(Area, created.id) is None
