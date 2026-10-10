"""Pruebas del módulo de planes."""

import uuid
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models.area import Area
from app.models.plan import Plan, plan_areas
from app.services.plan_service import (
    AreaNotFoundForPlanError,
    DuplicatePlanError,
    get_plan_by_id,
    list_plans,
    register_plan,
    update_plan,
)
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig


def _unique_name(prefix: str) -> str:
    """Genera un nombre único por prueba sin depender de nombres fijos."""
    suffix = "".join(ch for ch in uuid.uuid4().hex if ch.isalpha())[:8]
    return f"{prefix} {suffix}"


def _delete_exact_plan_ids(plan_ids):
    """Elimina solo los IDs exactos pasados, sin tocar registros previos."""
    if not plan_ids:
        return

    ids = list(plan_ids)
    db.session.execute(db.delete(plan_areas).where(plan_areas.c.plan_id.in_(ids)))
    db.session.execute(db.delete(Plan).where(Plan.id.in_(ids)))
    db.session.commit()


def _delete_exact_area_ids(area_ids):
    """Elimina solo los IDs exactos pasados para áreas relacionadas."""
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
def tracked_plan_ids(app):
    """Registra IDs de planes creados por cada prueba y los elimina al final."""
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_plan_ids(created_ids)


@pytest.fixture
def tracked_area_ids(app):
    """Registra IDs de áreas creadas por cada prueba y los elimina al final."""
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_area_ids(created_ids)


@pytest.fixture
def sample_areas(app, tracked_area_ids):
    """Devuelve áreas básicas para pruebas de planes."""
    with app.app_context():
        musculacion = Area(name=_unique_name("Area Musculación"))
        jumping = Area(name=_unique_name("Area Jumping"))
        bailoterapia = Area(name=_unique_name("Area Bailoterapia"))
        db.session.add_all([musculacion, jumping, bailoterapia])
        db.session.commit()
        tracked_area_ids.update({musculacion.id, jumping.id, bailoterapia.id})
        return [
            db.session.get(Area, musculacion.id),
            db.session.get(Area, jumping.id),
            db.session.get(Area, bailoterapia.id),
        ]


def test_register_plan_success(app, sample_areas, tracked_plan_ids):
    """Registra un plan con una o varias áreas."""
    with app.app_context():
        plan = register_plan(_unique_name("Plan Básico"), Decimal("25.00"), [sample_areas[0].id])
        tracked_plan_ids.add(plan.id)
        assert plan.id is not None
        assert plan.name.startswith("Plan Básico")
        assert plan.price == Decimal("25.00")
        assert len(plan.areas) == 1


def test_register_plan_rejects_invalid_name(app):
    """Rechaza nombres vacíos o inválidos."""
    with app.app_context():
        with pytest.raises(ValueError):
            register_plan("", Decimal("10.00"))


def test_register_plan_rejects_invalid_price(app, sample_areas):
    """Rechaza precios no válidos."""
    with app.app_context():
        with pytest.raises(ValueError):
            register_plan(_unique_name("Plan X"), "abc")
        with pytest.raises(ValueError):
            register_plan(_unique_name("Plan Y"), 0)


def test_register_plan_rejects_missing_area(app):
    """Rechaza áreas inexistentes."""
    with app.app_context():
        with pytest.raises(AreaNotFoundForPlanError):
            register_plan(_unique_name("Plan Invalido"), Decimal("10.00"), [9999])


def test_register_plan_rejects_duplicate_relations(app, sample_areas):
    """Evita duplicar la misma relación plan-área."""
    with app.app_context():
        plan = register_plan(_unique_name("Plan Full"), Decimal("40.00"), [sample_areas[0].id, sample_areas[1].id])
        with pytest.raises(Exception):
            plan.areas = [sample_areas[0], sample_areas[1], sample_areas[0]]


def test_list_plans(app, sample_areas, tracked_plan_ids):
    """Lista planes registrados."""
    with app.app_context():
        first = register_plan(_unique_name("Plan A"), Decimal("20.00"), [sample_areas[0].id])
        second = register_plan(_unique_name("Plan B"), Decimal("30.00"), [sample_areas[1].id, sample_areas[2].id])
        tracked_plan_ids.update({first.id, second.id})
        plans = list_plans()
        assert len(plans) >= 2


def test_get_plan_by_id(app, sample_areas, tracked_plan_ids):
    """Consulta un plan por ID."""
    with app.app_context():
        created = register_plan(_unique_name("Plan C"), Decimal("15.00"), [sample_areas[0].id])
        tracked_plan_ids.add(created.id)
        fetched = get_plan_by_id(created.id)
        assert fetched is not None
        assert fetched.name == created.name


def test_update_plan_success(app, sample_areas, tracked_plan_ids):
    """Actualiza nombre, precio y áreas de un plan."""
    with app.app_context():
        created = register_plan(_unique_name("Plan D"), Decimal("20.00"), [sample_areas[0].id])
        tracked_plan_ids.add(created.id)
        original_name = created.name
        updated = update_plan(
            created.id,
            name=f"{original_name} Plus",
            price="35.50",
            area_ids=[sample_areas[0].id, sample_areas[1].id],
        )
        assert updated.name == f"{original_name} Plus"
        assert updated.price == Decimal("35.50")
        assert len(updated.areas) == 2


def test_update_plan_rejects_duplicate_name(app, sample_areas, tracked_plan_ids):
    """Rechaza nombres duplicados al actualizar."""
    with app.app_context():
        first = register_plan(_unique_name("Plan E"), Decimal("22.00"), [sample_areas[0].id])
        second = register_plan(_unique_name("Plan F"), Decimal("25.00"), [sample_areas[1].id])
        tracked_plan_ids.update({first.id, second.id})
        with pytest.raises(DuplicatePlanError):
            update_plan(second.id, name=first.name)


def test_plan_api_endpoints(app, sample_areas, tracked_plan_ids, authenticated_client):
    """Prueba endpoints HTTP de planes."""
    client = authenticated_client
    name = _unique_name("Plan API")
    updated_name = _unique_name("Plan API Updated")

    with app.app_context():
        response = client.post(
            "/api/plans",
            json={
                "name": name,
                "price": "42.50",
                "area_ids": [sample_areas[0].id, sample_areas[1].id],
            },
        )
        assert response.status_code == 201
        payload = response.get_json()
        plan_id = payload["id"]
        tracked_plan_ids.add(plan_id)

        list_response = client.get("/api/plans")
        assert list_response.status_code == 200
        assert any(item["id"] == plan_id for item in list_response.get_json())

        get_response = client.get(f"/api/plans/{plan_id}")
        assert get_response.status_code == 200
        assert get_response.get_json()["name"] == name

        patch_response = client.patch(
            f"/api/plans/{plan_id}",
            json={"name": updated_name, "price": "60.00"},
        )
        assert patch_response.status_code == 200
        assert patch_response.get_json()["name"] == updated_name


def test_plan_api_http_errors(app, sample_areas, tracked_plan_ids, authenticated_client):
    """Verifica 400, 404 y 409 en la API de planes."""
    client = authenticated_client

    invalid_response = client.post(
        "/api/plans",
        json={"name": _unique_name("Plan X"), "price": "-1", "area_ids": [sample_areas[0].id]},
    )
    assert invalid_response.status_code == 400

    with app.app_context():
        first = register_plan(_unique_name("Plan Original"), Decimal("30.00"), [sample_areas[0].id])
        tracked_plan_ids.add(first.id)
        duplicate_response = client.post(
            "/api/plans",
            json={"name": first.name, "price": "31.00", "area_ids": [sample_areas[0].id]},
        )
        assert duplicate_response.status_code == 409

        missing_response = client.get("/api/plans/999999")
        assert missing_response.status_code == 404


def test_plan_history_conservation_is_not_broken(app, sample_areas, tracked_plan_ids):
    """La actualización del plan no altera sincrónicamente el historial de membresías (modelo no implementado aún)."""
    with app.app_context():
        plan = register_plan(_unique_name("Plan Historial"), Decimal("50.00"), [sample_areas[0].id])
        tracked_plan_ids.add(plan.id)
        original_name = plan.name
        updated = update_plan(plan.id, name=f"{original_name} Actualizado", price="60.00")
        assert updated.id == plan.id
        assert updated.name == f"{original_name} Actualizado"
        assert updated.price == Decimal("60.00")


def test_cleanup_does_not_delete_preexisting_plan(app, sample_areas, tracked_plan_ids):
    """La limpieza no elimina un plan previo con un nombre habitual."""
    with app.app_context():
        suffix = "".join(ch for ch in uuid.uuid4().hex if ch.isalpha())[:8]
        existing = Plan(name=f"Plan Base {suffix}", price=Decimal("20.00"))
        db.session.add(existing)
        db.session.commit()

        created = register_plan(_unique_name("Plan Isolation"), Decimal("42.50"), [sample_areas[0].id])
        tracked_plan_ids.add(created.id)

        assert db.session.get(Plan, existing.id) is not None
        assert db.session.get(Plan, created.id) is not None

        _delete_exact_plan_ids({created.id})

        assert db.session.get(Plan, existing.id) is not None
        assert db.session.get(Plan, created.id) is None
