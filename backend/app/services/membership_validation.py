"""
Reglas de validación de membresías de Active Gym.
"""

from datetime import date


def dates_overlap(
    first_start: date,
    first_end: date,
    second_start: date,
    second_end: date,
) -> bool:
    """
    Comprueba si dos períodos de fechas se superponen.

    Las fechas de inicio y vencimiento están incluidas.
    """

    if first_start > first_end:
        raise ValueError("El primer período tiene fechas inválidas.")

    if second_start > second_end:
        raise ValueError("El segundo período tiene fechas inválidas.")

    return (
        first_start <= second_end
        and second_start <= first_end
    )
def areas_overlap(
    first_area_ids: set[int],
    second_area_ids: set[int],
) -> bool:
    """
    Comprueba si dos conjuntos de áreas tienen
    al menos un identificador en común.
    """

    return bool(first_area_ids & second_area_ids)

def memberships_conflict(
    first_start: date,
    first_end: date,
    first_area_ids: set[int],
    second_start: date,
    second_end: date,
    second_area_ids: set[int],
) -> bool:
    """
    Determina si dos membresías tienen un conflicto.

    Existe conflicto cuando sus fechas se superponen
    y comparten al menos un área.

    Esta función supone que ambas membresías
    pertenecen al mismo cliente.
    """

    overlapping_dates = dates_overlap(
        first_start,
        first_end,
        second_start,
        second_end,
    )

    overlapping_areas = areas_overlap(
        first_area_ids,
        second_area_ids,
    )

    return overlapping_dates and overlapping_areas

def has_membership_conflict(
    existing_memberships,
    new_start: date,
    new_end: date,
    new_area_ids: set[int],
) -> bool:
    """
    Comprueba si una nueva inscripción entra en conflicto
    con las membresías existentes de un mismo cliente.

    existing_memberships debe contener únicamente
    membresías pertenecientes a ese cliente.
    """

    if new_start > new_end:
        raise ValueError(
            "La nueva membresía tiene fechas inválidas."
        )

    if not new_area_ids:
        raise ValueError(
            "La nueva membresía debe incluir al menos un área."
        )

    for membership in existing_memberships:

        existing_area_ids = {
            area.id
            for area in membership.areas
        }

        if memberships_conflict(
            first_start=membership.start_date,
            first_end=membership.end_date,
            first_area_ids=existing_area_ids,
            second_start=new_start,
            second_end=new_end,
            second_area_ids=new_area_ids,
        ):
            return True

    return False