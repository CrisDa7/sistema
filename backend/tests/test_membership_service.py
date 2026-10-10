"""Pruebas del módulo de membresías en la base de pruebas autorizada."""

import uuid
from datetime import date
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models.area import Area
from app.models.client import Client
from app.models.membership import Membership, membership_areas
from app.models.plan import Plan, plan_areas
from app.services.membership_service import (
    MembershipConflictError,
    get_membership_by_id,
    list_memberships,
    list_memberships_by_client,
    register_membership,
    register_reentry_membership,
    renew_membership_continuity,
)
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig


def _unique_name(prefix: str) -> str:
    suffix = "".join(ch for ch in uuid.uuid4().hex if ch.isalpha())[:8]
    return f"{prefix} {suffix}"


def _delete_exact_membership_ids(membership_ids):
    if not membership_ids:
        return
    ids = list(membership_ids)
    db.session.execute(db.delete(membership_areas).where(membership_areas.c.membership_id.in_(ids)))
    db.session.execute(db.delete(Membership).where(Membership.id.in_(ids)))
    db.session.commit()


def _delete_exact_client_ids(client_ids):
    if not client_ids:
        return
    ids = list(client_ids)
    db.session.execute(db.delete(membership_areas).where(membership_areas.c.membership_id.in_(
        db.session.execute(db.select(Membership.id).where(Membership.client_id.in_(ids))).scalars().all()
    )))
    db.session.execute(db.delete(Membership).where(Membership.client_id.in_(ids)))
    db.session.execute(db.delete(Client).where(Client.id.in_(ids)))
    db.session.commit()


def _delete_exact_plan_ids(plan_ids):
    if not plan_ids:
        return
    ids = list(plan_ids)
    membership_ids = db.session.execute(db.select(Membership.id).where(Membership.plan_id.in_(ids))).scalars().all()
    db.session.execute(db.delete(membership_areas).where(membership_areas.c.membership_id.in_(membership_ids)))
    db.session.execute(db.delete(Membership).where(Membership.plan_id.in_(ids)))
    db.session.execute(db.delete(plan_areas).where(plan_areas.c.plan_id.in_(ids)))
    db.session.execute(db.delete(Plan).where(Plan.id.in_(ids)))
    db.session.commit()


def _delete_exact_area_ids(area_ids):
    if not area_ids:
        return
    ids = list(area_ids)
    db.session.execute(db.delete(plan_areas).where(plan_areas.c.area_id.in_(ids)))
    db.session.execute(db.delete(membership_areas).where(membership_areas.c.area_id.in_(ids)))
    db.session.execute(db.delete(Area).where(Area.id.in_(ids)))
    db.session.commit()


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        ensure_test_database()
        yield app


@pytest.fixture
def tracked_membership_ids(app):
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_membership_ids(created_ids)


@pytest.fixture
def tracked_client_ids(app):
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_client_ids(created_ids)


@pytest.fixture
def tracked_plan_ids(app):
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_plan_ids(created_ids)


@pytest.fixture
def tracked_area_ids(app):
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_area_ids(created_ids)


@pytest.fixture
def sample_client(app, tracked_client_ids):
    with app.app_context():
        client = Client(
            cedula="1700000001",
            first_name="Ana",
            last_name="Pérez",
            phone="0999999999",
        )
        db.session.add(client)
        db.session.commit()
        tracked_client_ids.add(client.id)
        return client


@pytest.fixture
def sample_areas(app, tracked_area_ids):
    with app.app_context():
        areas = [
            Area(name=_unique_name("Area Musculación")),
            Area(name=_unique_name("Area Bailoterapia")),
            Area(name=_unique_name("Area Yoga")),
        ]
        db.session.add_all(areas)
        db.session.commit()
        tracked_area_ids.update(area.id for area in areas)
        return areas


@pytest.fixture
def sample_plan(app, sample_areas, tracked_plan_ids):
    with app.app_context():
        plan = Plan(name=_unique_name("Plan Premium"), price=Decimal("40.00"), areas=sample_areas[:2])
        db.session.add(plan)
        db.session.commit()
        tracked_plan_ids.add(plan.id)
        return plan


def test_register_membership_success(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        membership = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[area.id for area in db.session.get(Plan, sample_plan.id).areas],
            contracted_price="45.50",
        )
        tracked_membership_ids.add(membership.id)
        assert membership.start_date == date(2026, 11, 10)
        assert membership.end_date == date(2026, 12, 9)
        assert membership.contracted_price == Decimal("45.50")
        assert {area.id for area in membership.areas} == {area.id for area in db.session.get(Plan, sample_plan.id).areas}


def test_membership_registration_uses_training_start_not_payment_date(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        membership = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="35.00",
        )
        tracked_membership_ids.add(membership.id)
        assert membership.start_date == date(2026, 11, 10)
        assert membership.contracted_price == Decimal("35.00")


def test_register_membership_rejects_conflict_in_same_area(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        first = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(first.id)

        with pytest.raises(MembershipConflictError):
            register_membership(
                client_id=sample_client.id,
                plan_id=sample_plan.id,
                start_date=date(2026, 11, 20),
                end_date=date(2026, 12, 19),
                area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
                contracted_price="30.00",
            )


def test_register_membership_allows_different_area_overlap(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        first = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(first.id)

        second = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 15),
            end_date=date(2026, 12, 14),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[1].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(second.id)

        assert second is not None


def test_membership_list_by_client(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        first = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        second = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 12, 10),
            end_date=date(2027, 1, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[1].id],
            contracted_price="35.00",
        )
        tracked_membership_ids.update({first.id, second.id})

        memberships = list_memberships_by_client(sample_client.id)
        assert {membership.id for membership in memberships} >= {first.id, second.id}


def test_membership_api_http_codes(app, sample_client, sample_plan, tracked_membership_ids, authenticated_client):
    client = authenticated_client

    with app.app_context():
        response = client.post(
            "/api/memberships",
            json={
                "client_id": sample_client.id,
                "plan_id": sample_plan.id,
                "start_date": "2026-11-10",
                "end_date": "2026-12-09",
                "area_ids": [db.session.get(Plan, sample_plan.id).areas[0].id],
                "contracted_price": "50.00",
            },
        )
        assert response.status_code == 201
        payload = response.get_json()
        tracked_membership_ids.add(payload["id"])

        invalid_response = client.post(
            "/api/memberships",
            json={
                "client_id": 999999,
                "plan_id": sample_plan.id,
                "start_date": "2026-11-10",
                "end_date": "2026-12-09",
                "area_ids": [db.session.get(Plan, sample_plan.id).areas[0].id],
                "contracted_price": "50.00",
            },
        )
        assert invalid_response.status_code == 404

        conflict_response = client.post(
            "/api/memberships",
            json={
                "client_id": sample_client.id,
                "plan_id": sample_plan.id,
                "start_date": "2026-11-20",
                "end_date": "2026-12-19",
                "area_ids": [db.session.get(Plan, sample_plan.id).areas[0].id],
                "contracted_price": "50.00",
            },
        )
        assert conflict_response.status_code == 409

        get_response = client.get(f"/api/memberships/{payload['id']}")
        assert get_response.status_code == 200
        assert get_response.get_json()["id"] == payload["id"]


def test_membership_route_by_client_is_exact(app, sample_client, sample_plan, tracked_membership_ids, authenticated_client):
    client = authenticated_client
    with app.app_context():
        membership = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(membership.id)

        response = client.get(f"/api/clients/{sample_client.id}/memberships")
        assert response.status_code == 200
        payload = response.get_json()
        assert any(item["id"] == membership.id for item in payload)


def test_renewal_api_conflict_and_not_found(app, sample_client, sample_plan, tracked_membership_ids, authenticated_client):
    client = authenticated_client
    with app.app_context():
        old = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(old.id)

        conflict_response = client.post(
            f"/api/memberships/{old.id}/renew",
            json={"mode": "continuity", "area_ids": [db.session.get(Plan, sample_plan.id).areas[0].id]},
        )
        assert conflict_response.status_code == 201

        missing_response = client.post(
            "/api/memberships/999999/renew",
            json={"mode": "continuity", "area_ids": [db.session.get(Plan, sample_plan.id).areas[0].id]},
        )
        assert missing_response.status_code == 404

        invalid_mode = client.post(
            f"/api/memberships/{old.id}/renew",
            json={"mode": "bad-mode", "area_ids": [db.session.get(Plan, sample_plan.id).areas[0].id]},
        )
        assert invalid_mode.status_code == 400


def test_reentry_uses_real_return_date(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        new_membership = register_reentry_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2027, 1, 15),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="40.00",
        )
        tracked_membership_ids.add(new_membership.id)

        assert new_membership.start_date == date(2027, 1, 15)
        assert new_membership.end_date == date(2027, 2, 14)
        assert new_membership.contracted_price == Decimal("40.00")


def test_renewal_preserves_previous_membership_history(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        old = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(old.id)

        renewed = renew_membership_continuity(
            membership_id=old.id,
            renewal_date=date(2026, 12, 15),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="35.00",
        )
        tracked_membership_ids.add(renewed.id)

        assert db.session.get(Membership, old.id).id == old.id
        assert db.session.get(Membership, renewed.id).id == renewed.id
        assert db.session.get(Membership, old.id).contracted_price == Decimal("30.00")
        assert db.session.get(Membership, renewed.id).contracted_price == Decimal("35.00")


def test_reentry_without_area_and_price_reuses_previous_membership(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        previous = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(previous.id)

        reentry = register_reentry_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2027, 1, 15),
            previous_membership_id=previous.id,
        )
        tracked_membership_ids.add(reentry.id)

        assert reentry.start_date == date(2027, 1, 15)
        assert reentry.end_date == date(2027, 2, 14)
        assert reentry.contracted_price == Decimal("30.00")
        assert {area.id for area in reentry.areas} == {area.id for area in previous.areas}
        assert db.session.get(Membership, previous.id).id == previous.id


def test_reentry_with_custom_price(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        previous = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(previous.id)

        reentry = register_reentry_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2027, 1, 15),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="42.50",
            previous_membership_id=previous.id,
        )
        tracked_membership_ids.add(reentry.id)

        assert reentry.contracted_price == Decimal("42.50")
        assert reentry.start_date == date(2027, 1, 15)
        assert reentry.end_date == date(2027, 2, 14)
        assert db.session.get(Membership, previous.id).contracted_price == Decimal("30.00")


def test_reentry_with_different_areas(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        previous = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(previous.id)

        reentry = register_reentry_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2027, 1, 15),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[1].id],
            contracted_price=None,
            previous_membership_id=previous.id,
        )
        tracked_membership_ids.add(reentry.id)

        assert {area.id for area in reentry.areas} == {db.session.get(Plan, sample_plan.id).areas[1].id}
        assert reentry.contracted_price == Decimal("30.00")


def test_reentry_keeps_previous_membership_history(app, sample_client, sample_plan, tracked_membership_ids):
    with app.app_context():
        previous = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=[db.session.get(Plan, sample_plan.id).areas[0].id],
            contracted_price="30.00",
        )
        tracked_membership_ids.add(previous.id)

        reentry = register_reentry_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2027, 1, 15),
            previous_membership_id=previous.id,
        )
        tracked_membership_ids.add(reentry.id)

        assert previous.id != reentry.id
        assert db.session.get(Membership, previous.id).contracted_price == Decimal("30.00")
        assert db.session.get(Membership, previous.id).start_date == date(2026, 11, 10)
        assert db.session.get(Membership, reentry.id).start_date == date(2027, 1, 15)
