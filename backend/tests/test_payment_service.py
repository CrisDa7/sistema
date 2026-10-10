"""Pruebas del módulo de pagos en la base de pruebas autorizada."""

import uuid
from datetime import date
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models.area import Area
from app.models.client import Client
from app.models.membership import Membership, membership_areas
from app.models.payment import Payment
from app.models.plan import Plan, plan_areas
from app.services.membership_service import register_membership
from app.services.payment_service import (
    DuplicatePaymentError,
    DuplicateTransferReferenceError,
    MembershipNotFoundForPaymentError,
    register_payment,
)
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig


def _unique_name(prefix: str) -> str:
    suffix = "".join(ch for ch in uuid.uuid4().hex if ch.isalpha())[:8]
    return f"{prefix} {suffix}"


def _ensure_payments_table() -> None:
    db.session.execute(
        db.text(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                membership_id INTEGER NOT NULL UNIQUE,
                amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
                payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('cash', 'bank_transfer')),
                payment_date DATE NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                transfer_reference VARCHAR(100),
                observations TEXT,
                CONSTRAINT fk_payments_membership
                    FOREIGN KEY (membership_id)
                    REFERENCES memberships(id)
                    ON DELETE RESTRICT
            );
            """
        )
    )
    db.session.execute(
        db.text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ix_payments_transfer_reference_unique
            ON payments (transfer_reference)
            WHERE transfer_reference IS NOT NULL;
            """
        )
    )
    db.session.commit()


def _delete_exact_payment_ids(payment_ids):
    if not payment_ids:
        return
    ids = list(payment_ids)
    db.session.execute(db.delete(Payment).where(Payment.id.in_(ids)))
    db.session.commit()


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
    membership_ids = db.session.execute(db.select(Membership.id).where(Membership.client_id.in_(ids))).scalars().all()
    db.session.execute(db.delete(membership_areas).where(membership_areas.c.membership_id.in_(membership_ids)))
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
        _ensure_payments_table()
        yield app


@pytest.fixture
def tracked_payment_ids(app):
    created_ids = set()
    yield created_ids
    with app.app_context():
        ensure_test_database()
        _delete_exact_payment_ids(created_ids)


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
            Area(name=_unique_name("Area Gimnasio")),
            Area(name=_unique_name("Area Yoga")),
        ]
        db.session.add_all(areas)
        db.session.commit()
        tracked_area_ids.update(area.id for area in areas)
        return areas


@pytest.fixture
def sample_plan(app, sample_areas, tracked_plan_ids):
    with app.app_context():
        plan = Plan(name=_unique_name("Plan Premium"), price=Decimal("180.00"), areas=sample_areas)
        db.session.add(plan)
        db.session.commit()
        tracked_plan_ids.add(plan.id)
        return plan


@pytest.fixture
def sample_membership(app, sample_client, sample_plan, sample_areas, tracked_membership_ids):
    with app.app_context():
        plan = db.session.get(Plan, sample_plan.id)
        area_ids = [area.id for area in plan.areas]
        membership = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 12, 9),
            area_ids=area_ids,
            contracted_price=Decimal("180.00"),
        )
        tracked_membership_ids.add(membership.id)
        return membership


def test_register_payment_cash_success(app, sample_membership, tracked_payment_ids):
    with app.app_context():
        payment = register_payment(
            membership_id=sample_membership.id,
            amount=Decimal("180.00"),
            payment_method="cash",
            payment_date=date(2026, 10, 21),
        )
        tracked_payment_ids.add(payment.id)

        assert payment.amount == Decimal("180.00")
        assert payment.payment_method == "cash"
        assert payment.transfer_reference is None
        assert payment.membership_id == sample_membership.id


def test_register_payment_bank_transfer_success(app, sample_membership, tracked_payment_ids):
    with app.app_context():
        payment = register_payment(
            membership_id=sample_membership.id,
            amount=Decimal("180.00"),
            payment_method="bank_transfer",
            payment_date=date(2026, 10, 22),
            transfer_reference=" trf 001 123 ",
        )
        tracked_payment_ids.add(payment.id)

        assert payment.amount == Decimal("180.00")
        assert payment.payment_method == "bank_transfer"
        assert payment.transfer_reference == "TRF001123"


def test_register_payment_requires_transfer_reference(app, sample_membership):
    with app.app_context():
        with pytest.raises(ValueError, match="transferencia"):
            register_payment(
                membership_id=sample_membership.id,
                amount=Decimal("180.00"),
                payment_method="bank_transfer",
                payment_date=date(2026, 10, 23),
                transfer_reference="   ",
            )


def test_register_payment_rejects_duplicate_transfer_reference(app, sample_membership, tracked_payment_ids):
    with app.app_context():
        first = register_payment(
            membership_id=sample_membership.id,
            amount=Decimal("180.00"),
            payment_method="bank_transfer",
            payment_date=date(2026, 10, 24),
            transfer_reference="REF-123",
        )
        tracked_payment_ids.add(first.id)

        plan = db.session.get(Plan, sample_membership.plan_id)
        area_ids = [area.id for area in plan.areas]
        second_membership = register_membership(
            client_id=sample_membership.client_id,
            plan_id=sample_membership.plan_id,
            start_date=date(2026, 12, 10),
            end_date=date(2027, 1, 9),
            area_ids=area_ids,
            contracted_price=Decimal("180.00"),
        )

        with pytest.raises(DuplicateTransferReferenceError):
            register_payment(
                membership_id=second_membership.id,
                amount=Decimal("180.00"),
                payment_method="bank_transfer",
                payment_date=date(2026, 10, 25),
                transfer_reference="ref-123",
            )


def test_register_payment_rejects_amount_mismatch(app, sample_membership):
    with app.app_context():
        with pytest.raises(ValueError, match="precio contratado"):
            register_payment(
                membership_id=sample_membership.id,
                amount=Decimal("160.00"),
                payment_method="cash",
                payment_date=date(2026, 10, 26),
            )


@pytest.mark.parametrize("amount", [Decimal("0.00"), Decimal("-10.00"), "invalid", ""])
def test_register_payment_rejects_invalid_amount(app, sample_membership, amount):
    with app.app_context():
        with pytest.raises(ValueError):
            register_payment(
                membership_id=sample_membership.id,
                amount=amount,
                payment_method="cash",
                payment_date=date(2026, 10, 27),
            )


def test_register_payment_rejects_invalid_method(app, sample_membership):
    with app.app_context():
        with pytest.raises(ValueError):
            register_payment(
                membership_id=sample_membership.id,
                amount=Decimal("180.00"),
                payment_method="credit_card",
                payment_date=date(2026, 10, 28),
            )


def test_register_payment_membership_not_found(app):
    with app.app_context():
        with pytest.raises(MembershipNotFoundForPaymentError):
            register_payment(
                membership_id=999999,
                amount=Decimal("180.00"),
                payment_method="cash",
                payment_date=date(2026, 10, 29),
            )


def test_second_payment_rejected(app, sample_membership, tracked_payment_ids):
    with app.app_context():
        first = register_payment(
            membership_id=sample_membership.id,
            amount=Decimal("180.00"),
            payment_method="cash",
            payment_date=date(2026, 10, 30),
        )
        tracked_payment_ids.add(first.id)

        with pytest.raises(DuplicatePaymentError):
            register_payment(
                membership_id=sample_membership.id,
                amount=Decimal("180.00"),
                payment_method="cash",
                payment_date=date(2026, 10, 31),
            )


def test_payment_status_false_when_membership_has_no_payment(app, sample_membership, authenticated_client):
    with app.app_context():
        status = db.session.execute(db.select(Payment)).scalar()
        assert status is None

        response = authenticated_client.get(f"/api/memberships/{sample_membership.id}/payment-status")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["paid"] is False
        assert payload["payment_id"] is None
        assert payload["contracted_price"] == "180.00"


def test_payment_status_true_when_membership_has_payment(app, sample_membership, tracked_payment_ids, authenticated_client):
    with app.app_context():
        payment = register_payment(
            membership_id=sample_membership.id,
            amount=Decimal("180.00"),
            payment_method="cash",
            payment_date=date(2026, 11, 1),
        )
        tracked_payment_ids.add(payment.id)

        response = authenticated_client.get(f"/api/memberships/{sample_membership.id}/payment-status")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["paid"] is True
        assert payload["payment_id"] == payment.id


def test_payment_for_future_membership(app, sample_client, sample_plan, tracked_membership_ids, tracked_payment_ids):
    with app.app_context():
        plan = db.session.get(Plan, sample_plan.id)
        area_ids = [area.id for area in plan.areas]
        future_membership = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2028, 1, 10),
            end_date=date(2028, 2, 9),
            area_ids=area_ids,
            contracted_price=Decimal("180.00"),
        )
        tracked_membership_ids.add(future_membership.id)

        payment = register_payment(
            membership_id=future_membership.id,
            amount=Decimal("180.00"),
            payment_method="cash",
            payment_date=date(2027, 12, 15),
        )
        tracked_payment_ids.add(payment.id)

        assert payment.payment_date == date(2027, 12, 15)
        assert future_membership.start_date == date(2028, 1, 10)


def test_payment_for_expired_membership(app, sample_client, sample_plan, tracked_membership_ids, tracked_payment_ids):
    with app.app_context():
        plan = db.session.get(Plan, sample_plan.id)
        area_ids = [area.id for area in plan.areas]
        expired_membership = register_membership(
            client_id=sample_client.id,
            plan_id=sample_plan.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            area_ids=area_ids,
            contracted_price=Decimal("180.00"),
        )
        tracked_membership_ids.add(expired_membership.id)

        payment = register_payment(
            membership_id=expired_membership.id,
            amount=Decimal("180.00"),
            payment_method="cash",
            payment_date=date(2026, 6, 20),
        )
        tracked_payment_ids.add(payment.id)

        assert payment.payment_date == date(2026, 6, 20)
        assert expired_membership.end_date == date(2024, 1, 31)


def test_payment_date_is_independent_from_membership_dates(app, sample_membership, tracked_payment_ids):
    with app.app_context():
        payment = register_payment(
            membership_id=sample_membership.id,
            amount=Decimal("180.00"),
            payment_method="cash",
            payment_date=date(2030, 2, 14),
        )
        tracked_payment_ids.add(payment.id)

        assert payment.payment_date == date(2030, 2, 14)
        assert sample_membership.start_date == date(2026, 11, 10)
        assert sample_membership.end_date == date(2026, 12, 9)


def test_payment_does_not_modify_historical_membership_data(app, sample_membership, tracked_payment_ids):
    with app.app_context():
        membership = db.session.get(Membership, sample_membership.id)
        original_contracted = membership.contracted_price
        original_start = membership.start_date
        original_end = membership.end_date
        original_areas = [area.id for area in membership.areas]

        payment = register_payment(
            membership_id=membership.id,
            amount=Decimal("180.00"),
            payment_method="cash",
            payment_date=date(2026, 10, 15),
        )
        tracked_payment_ids.add(payment.id)

        db.session.refresh(membership)
        assert membership.contracted_price == original_contracted
        assert membership.start_date == original_start
        assert membership.end_date == original_end
        assert [area.id for area in membership.areas] == original_areas


def test_membership_payment_endpoints(app, sample_membership, tracked_payment_ids, authenticated_client):
    client = authenticated_client

    with app.app_context():
        response = client.post(
            f"/api/memberships/{sample_membership.id}/payments",
            json={
                "amount": "180.00",
                "payment_method": "cash",
                "payment_date": "2026-10-20",
            },
        )
        assert response.status_code == 201
        payload = response.get_json()
        tracked_payment_ids.add(payload["id"])
        assert payload["amount"] == "180.00"

        list_response = client.get(f"/api/memberships/{sample_membership.id}/payments")
        assert list_response.status_code == 200
        assert len(list_response.get_json()) == 1

        detail_response = client.get(f"/api/payments/{payload['id']}")
        assert detail_response.status_code == 200
        assert detail_response.get_json()["id"] == payload["id"]

        status_response = client.get(f"/api/memberships/{sample_membership.id}/payment-status")
        assert status_response.status_code == 200
        status_payload = status_response.get_json()
        assert status_payload["paid"] is True
        assert status_payload["contracted_price"] == "180.00"


def test_cleanup_does_not_delete_preexisting_data(app, sample_membership, tracked_payment_ids):
    with app.app_context():
        existing_payment = Payment(
            membership_id=sample_membership.id,
            amount=Decimal("180.00"),
            payment_method="cash",
            payment_date=date(2026, 10, 10),
        )
        db.session.add(existing_payment)
        db.session.commit()
        tracked_payment_ids.add(existing_payment.id)

        assert db.session.get(Payment, existing_payment.id) is not None
        _delete_exact_payment_ids({existing_payment.id})
        assert db.session.get(Payment, existing_payment.id) is None
