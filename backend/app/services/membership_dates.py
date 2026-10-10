"""
Reglas de cálculo de fechas para membresías de Active Gym.

Contiene funciones para calcular períodos mensuales
sin depender de Flask ni de PostgreSQL.
"""

import calendar

from datetime import date, timedelta


def calculate_expiration_date(start_date: date) -> date:
    """
    Calcula el último día de vigencia de una membresía.

    La membresía dura un mes calendario y su fecha
    de vencimiento está incluida en el período.

    Si el mes siguiente no tiene el mismo día de inicio,
    se utiliza su último día disponible antes de restar
    un día.

    Args:
        start_date: Fecha en que comienza la membresía.

    Returns:
        date: Último día de vigencia de la membresía.

    Example:
        2026-10-10 -> 2026-11-09
    """

    # Calcular el mes y el año siguientes.
    if start_date.month == 12:
        next_month = 1
        next_year = start_date.year + 1
    else:
        next_month = start_date.month + 1
        next_year = start_date.year

    # Obtener la cantidad de días del mes siguiente.
    last_day_of_next_month = calendar.monthrange(
        next_year,
        next_month,
    )[1]

    # Ajustar el día si el mes siguiente es más corto.
    anniversary_day = min(
        start_date.day,
        last_day_of_next_month,
    )

    # Construir la fecha del aniversario mensual.
    next_anniversary = date(
        next_year,
        next_month,
        anniversary_day,
    )

    # El vencimiento es el día anterior al aniversario.
    expiration_date = next_anniversary - timedelta(days=1)

    return expiration_date


def calculate_renewal_start_date(
    previous_expiration_date: date,
    renewal_date: date,
) -> date:
    """
    Calcula la fecha de inicio de una renovación por continuidad.

    Para continuidad, el nuevo período comienza siempre
    el día siguiente al último día pagado de la membresía
    anterior, sin importar la fecha de registro de la operación.
    """

    return previous_expiration_date + timedelta(days=1)