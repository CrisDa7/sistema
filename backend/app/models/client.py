"""
Modelo de clientes de Active Gym.

Define la estructura de los datos personales básicos
de los clientes registrados en el gimnasio.
"""

from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Client(db.Model):
    """
    Representa a un cliente registrado en Active Gym.

    Attributes:
        id: Identificador único del cliente.
        cedula: Cédula ecuatoriana única del cliente.
        first_name: Nombres del cliente.
        last_name: Apellidos del cliente.
        phone: Número telefónico de contacto.
        registration_date: Fecha de registro del cliente.
    """

    __tablename__ = "clients"

    # Identificador único generado automáticamente.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    # Cédula ecuatoriana del cliente. Debe ser única.
    cedula: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
    )

    # Nombres del cliente. Campo obligatorio.
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Apellidos del cliente. Campo obligatorio.
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Teléfono almacenado como texto para admitir prefijos.
    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Fecha de registro, asignada al crear el cliente.
    registration_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    def __repr__(self) -> str:
        """
        Devuelve una representación útil para depuración.

        Returns:
            str: Identificador y nombre del cliente.
        """
        return (
            f"<Client id={self.id} "
            f"name='{self.first_name} {self.last_name}'>"
        )