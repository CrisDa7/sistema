"""Servicios para el módulo de áreas de Active Gym."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.area import Area
from app.validators.area_validator import validate_area_name


class AreaError(ValueError):
    """Error base del dominio de áreas."""


class DuplicateAreaError(AreaError):
    """Se lanza cuando el nombre del área ya existe."""


class AreaNotFoundError(AreaError):
    """Se lanza cuando el área no existe."""


def register_area(name: str) -> Area:
    """Registra un área con validación y unicidad."""
    normalized_name = validate_area_name(name)
    existing = db.session.execute(
        select(Area).where(db.func.lower(Area.name) == normalized_name.lower())
    ).scalar_one_or_none()

    if existing is not None:
        raise DuplicateAreaError("Ya existe un área registrada con este nombre.")

    area = Area(name=normalized_name)
    try:
        db.session.add(area)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DuplicateAreaError("Ya existe un área registrada con este nombre.") from exc

    return area


def get_area_by_id(area_id: int) -> Area | None:
    """Obtiene un área por su identificador."""
    return db.session.get(Area, area_id)


def list_areas() -> list[Area]:
    """Lista todas las áreas ordenadas por id."""
    return list(db.session.execute(select(Area).order_by(Area.id)).scalars().all())


def update_area(area_id: int, name: str | None = None) -> Area:
    """Actualiza el nombre de un área, respetando validación y unicidad."""
    area = db.session.get(Area, area_id)
    if area is None:
        raise AreaNotFoundError("El área no existe.")

    if name is None:
        raise ValueError("Debe enviar un nombre válido para actualizar.")

    normalized_name = validate_area_name(name)
    if normalized_name.lower() != area.name.lower():
        existing = db.session.execute(
            select(Area).where(db.func.lower(Area.name) == normalized_name.lower())
        ).scalar_one_or_none()
        if existing is not None and existing.id != area.id:
            raise DuplicateAreaError("Ya existe un área registrada con este nombre.")

    area.name = normalized_name
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DuplicateAreaError("Ya existe un área registrada con este nombre.") from exc

    return area
