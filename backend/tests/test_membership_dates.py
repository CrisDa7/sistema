"""
Pruebas unitarias del cálculo de fechas de membresías.

Verifica el vencimiento mensual, los cambios de año
y los meses con diferente cantidad de días.
"""

from datetime import date

import pytest

from app.services.membership_dates import (
    calculate_expiration_date,
    calculate_renewal_start_date,

)


@pytest.mark.parametrize(
    "start_date, expected_expiration",
    [
        (date(2026, 10, 10), date(2026, 11, 9)),
        (date(2027, 3, 15), date(2027, 4, 14)),
        (date(2027, 1, 31), date(2027, 2, 27)),
        (date(2028, 1, 31), date(2028, 2, 28)),
        (date(2026, 12, 10), date(2027, 1, 9)),
    ],
)
def test_calculate_expiration_date(
    start_date,
    expected_expiration,
):
    """
    Verifica que el vencimiento calculado coincida
    con la regla comercial de Active Gym.
    """

    result = calculate_expiration_date(start_date)

    assert result == expected_expiration


@pytest.mark.parametrize(
    "previous_expiration, renewal_date, expected_start",
    [
        (
            date(2026, 11, 9),
            date(2026, 11, 5),
            date(2026, 11, 10),
        ),
        (
            date(2026, 11, 9),
            date(2026, 11, 9),
            date(2026, 11, 10),
        ),
        (
            date(2026, 11, 9),
            date(2026, 11, 10),
            date(2026, 11, 10),
        ),
        (
            date(2026, 11, 9),
            date(2026, 11, 15),
            date(2026, 11, 10),
        ),
    ],
)
def test_calculate_renewal_start_date(
    previous_expiration,
    renewal_date,
    expected_start,
):
    """
    Verifica el inicio de las renovaciones anticipadas,
    realizadas al vencer y realizadas después de vencer.
    """

    result = calculate_renewal_start_date(
        previous_expiration,
        renewal_date,
    )

    assert result == expected_start