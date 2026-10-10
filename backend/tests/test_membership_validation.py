"""
Pruebas unitarias de validación de membresías.
"""

from datetime import date

import pytest
from decimal import Decimal

from app.models import Area, Membership

from app.services.membership_validation import areas_overlap, dates_overlap, memberships_conflict, has_membership_conflict


@pytest.mark.parametrize(
    "first_start, first_end, second_start, second_end, expected",
    [
        # Fechas superpuestas.
        (
            date(2026, 10, 10),
            date(2026, 11, 9),
            date(2026, 10, 20),
            date(2026, 11, 19),
            True,
        ),

        # La nueva membresía comienza al día siguiente.
        (
            date(2026, 10, 10),
            date(2026, 11, 9),
            date(2026, 11, 10),
            date(2026, 12, 9),
            False,
        ),

        # Coinciden exactamente en el último día.
        (
            date(2026, 10, 10),
            date(2026, 11, 9),
            date(2026, 11, 9),
            date(2026, 12, 8),
            True,
        ),

        # La nueva membresía corresponde a fechas anteriores.
        (
            date(2026, 10, 10),
            date(2026, 11, 9),
            date(2026, 9, 1),
            date(2026, 9, 30),
            False,
        ),

        # Períodos exactamente iguales.
        (
            date(2026, 10, 10),
            date(2026, 11, 9),
            date(2026, 10, 10),
            date(2026, 11, 9),
            True,
        ),
    ],
)
def test_dates_overlap(
    first_start,
    first_end,
    second_start,
    second_end,
    expected,
):
    """Verifica cuándo dos períodos se superponen."""

    result = dates_overlap(
        first_start,
        first_end,
        second_start,
        second_end,
    )

    assert result is expected


def test_dates_overlap_rejects_invalid_period():
    """Comprueba que se rechacen períodos inválidos."""

    with pytest.raises(ValueError):
        dates_overlap(
            date(2026, 11, 10),
            date(2026, 11, 9),
            date(2026, 12, 1),
            date(2026, 12, 31),
        )


@pytest.mark.parametrize(
    "first_areas, second_areas, expected",
    [
        ({2}, {3}, False),
        ({1, 3}, {2}, False),
        ({1, 3}, {3}, True),
        ({2}, {2}, True),
        ({1, 2}, {2, 3}, True),
        ({1}, set(), False),
    ],
)
def test_areas_overlap(
    first_areas,
    second_areas,
    expected,
):
    """Verifica si dos membresías comparten áreas."""

    result = areas_overlap(
        first_areas,
        second_areas,
    )

    assert result is expected


@pytest.mark.parametrize(
    "second_start, second_end, second_areas, expected",
    [
        # Jumping durante las mismas fechas: permitido.
        (
            date(2026, 10, 10),
            date(2026, 11, 9),
            {3},
            False,
        ),

        # Musculación con fechas superpuestas: permitido.
        (
            date(2026, 10, 20),
            date(2026, 11, 19),
            {1},
            False,
        ),

        # Bailoterapia con fechas superpuestas: conflicto.
        (
            date(2026, 10, 20),
            date(2026, 11, 19),
            {2},
            True,
        ),

        # Bailoterapia después del vencimiento: permitido.
        (
            date(2026, 11, 10),
            date(2026, 12, 9),
            {2},
            False,
        ),

        # Plan combinado que repite Bailoterapia: conflicto.
        (
            date(2026, 10, 20),
            date(2026, 11, 19),
            {2, 3},
            True,
        ),
    ],
)
def test_memberships_conflict(
    second_start,
    second_end,
    second_areas,
    expected,
):
    """
    Verifica conflictos entre membresías
    de un mismo cliente.
    """

    result = memberships_conflict(
        first_start=date(2026, 10, 10),
        first_end=date(2026, 11, 9),
        first_area_ids={2},
        second_start=second_start,
        second_end=second_end,
        second_area_ids=second_areas,
    )

    assert result is expected


def test_has_membership_conflict_with_different_areas():
    """
    Permite contratar Musculación cuando el cliente
    ya tiene Bailoterapia y Jumping.
    """

    bailoterapia = Area(id=2, name="Bailoterapia")
    jumping = Area(id=3, name="Jumping")

    membership_bailoterapia = Membership(
        client_id=1,
        plan_id=1,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 11, 9),
        contracted_price=Decimal("20.00"),
        areas=[bailoterapia],
    )

    membership_jumping = Membership(
        client_id=1,
        plan_id=2,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 11, 9),
        contracted_price=Decimal("20.00"),
        areas=[jumping],
    )

    existing_memberships = [
        membership_bailoterapia,
        membership_jumping,
    ]

    result = has_membership_conflict(
        existing_memberships=existing_memberships,
        new_start=date(2026, 10, 20),
        new_end=date(2026, 11, 19),
        new_area_ids={1},
    )

    assert result is False


def test_has_membership_conflict_with_same_area():
    """
    Rechaza una inscripción cuando el cliente
    ya tiene la misma área en fechas superpuestas.
    """

    bailoterapia = Area(
        id=2,
        name="Bailoterapia",
    )

    existing_membership = Membership(
        client_id=1,
        plan_id=1,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 11, 9),
        contracted_price=Decimal("20.00"),
        areas=[bailoterapia],
    )

    result = has_membership_conflict(
        existing_memberships=[existing_membership],
        new_start=date(2026, 10, 20),
        new_end=date(2026, 11, 19),
        new_area_ids={2},
    )

    assert result is True

def test_has_membership_conflict_after_expiration():
    """
    Permite una nueva inscripción a la misma área
    cuando comienza después del vencimiento.
    """

    bailoterapia = Area(
        id=2,
        name="Bailoterapia",
    )

    existing_membership = Membership(
        client_id=1,
        plan_id=1,
        start_date=date(2026, 10, 10),
        end_date=date(2026, 11, 9),
        contracted_price=Decimal("20.00"),
        areas=[bailoterapia],
    )

    result = has_membership_conflict(
        existing_memberships=[existing_membership],
        new_start=date(2026, 11, 10),
        new_end=date(2026, 12, 9),
        new_area_ids={2},
    )

    assert result is False
def test_has_membership_conflict_rejects_invalid_dates():
    """
    Rechaza una inscripción cuando el vencimiento
    es anterior a la fecha de inicio.
    """

    with pytest.raises(
        ValueError,
        match="fechas inválidas",
    ):
        has_membership_conflict(
            existing_memberships=[],
            new_start=date(2026, 11, 20),
            new_end=date(2026, 11, 10),
            new_area_ids={2},
        )

def test_has_membership_conflict_rejects_empty_areas():
    """
    Rechaza una inscripción que no tenga
    ninguna actividad seleccionada.
    """

    with pytest.raises(
        ValueError,
        match="al menos un área",
    ):
        has_membership_conflict(
            existing_memberships=[],
            new_start=date(2026, 11, 10),
            new_end=date(2026, 12, 9),
            new_area_ids=set(),
        )