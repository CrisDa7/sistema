"""Servicios para el registro y consulta de clientes de Active Gym."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.client import Client
from app.validators.client_validator import (
    validate_ecuadorian_cedula,
    validate_ecuadorian_phone,
    validate_person_name,
)


class ClientError(Exception):
    """Base de errores del dominio de clientes."""


class DuplicateCedulaError(ValueError):
    """Se lanza cuando la cédula ya está registrada."""


class ClientNotFoundError(ValueError):
    """Se lanza cuando un cliente no existe."""


def prepare_client(
    cedula: str,
    first_name: str,
    last_name: str,
    phone: str,
) -> Client:
    """Valida datos y devuelve una instancia de cliente preparada."""
    valid_cedula = validate_ecuadorian_cedula(cedula)
    valid_first_name = validate_person_name(first_name)
    valid_last_name = validate_person_name(last_name)
    valid_phone = validate_ecuadorian_phone(phone)

    return Client(
        cedula=valid_cedula,
        first_name=valid_first_name,
        last_name=valid_last_name,
        phone=valid_phone,
    )


def ensure_cedula_available(
    cedula: str,
    existing_cedulas: set[str],
) -> None:
    """Garantiza que una cédula válida aún no esté registrada."""
    valid_cedula = validate_ecuadorian_cedula(cedula)

    if valid_cedula in existing_cedulas:
        raise DuplicateCedulaError(
            "Ya existe un cliente registrado con esta cédula."
        )


def get_client_by_id(client_id: int) -> Client | None:
    """Devuelve un cliente por su identificador interno."""
    return db.session.get(Client, client_id)


def list_clients(search: str | None = None) -> list[Client]:
    """Lista clientes, opcionalmente filtrados por texto de búsqueda."""
    query = select(Client).order_by(Client.id)

    if search is not None:
        term = " ".join(search.strip().split())
        if term:
            query = query.where(
                or_(
                    Client.cedula.ilike(f"%{term}%"),
                    Client.first_name.ilike(f"%{term}%"),
                    Client.last_name.ilike(f"%{term}%"),
                )
            )

    return list(db.session.execute(query).scalars().all())


def search_clients(term: str) -> list[Client]:
    """Busca clientes por nombre, apellido o cédula."""
    normalized_term = " ".join((term or "").strip().split())
    return list_clients(normalized_term if normalized_term else None)


def register_client(
    cedula: str,
    first_name: str,
    last_name: str,
    phone: str,
) -> Client:
    """Valida y registra un cliente en PostgreSQL."""
    client = prepare_client(
        cedula=cedula,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )

    existing_client = db.session.execute(
        select(Client).where(Client.cedula == client.cedula)
    ).scalar_one_or_none()

    if existing_client is not None:
        raise DuplicateCedulaError(
            "Ya existe un cliente registrado con esta cédula."
        )

    try:
        db.session.add(client)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise DuplicateCedulaError(
            "Ya existe un cliente registrado con esta cédula."
        ) from error

    return client


def update_client(
    client_id: int,
    **changes: object,
) -> Client:
    """Actualiza los datos editables de un cliente sin tocar el registro original."""
    client = db.session.get(Client, client_id)

    if client is None:
        raise ClientNotFoundError("El cliente no existe.")

    if "id" in changes or "registration_date" in changes or "cedula" in changes:
        raise ValueError(
            "No se puede modificar el ID, la cédula ni la fecha de registro."
        )

    allowed_fields = {"first_name", "last_name", "phone"}
    invalid_fields = set(changes) - allowed_fields
    if invalid_fields:
        raise ValueError(
            "Los campos no permitidos para actualización son: "
            f"{', '.join(sorted(invalid_fields))}."
        )

    if not changes:
        raise ValueError("Debe enviar al menos un campo válido para actualizar.")

    for field, value in changes.items():
        if value is None:
            continue

        if field == "first_name":
            client.first_name = validate_person_name(str(value))
        elif field == "last_name":
            client.last_name = validate_person_name(str(value))
        elif field == "phone":
            client.phone = validate_ecuadorian_phone(str(value))

    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise ValueError(
            "No se pudo actualizar el cliente por un conflicto de integridad."
        ) from error

    return client