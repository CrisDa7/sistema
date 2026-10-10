"""Protecciones para las pruebas de base de datos."""

from sqlalchemy import text

from app.extensions import db


def ensure_test_database() -> None:
    """
    Impide operaciones de prueba fuera de active_gym_test_db.

    Debe ejecutarse dentro del contexto de Flask,
    antes de crear o eliminar tablas de pruebas.
    """

    database_name = db.session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    if database_name != "active_gym_test_db":
        raise RuntimeError(
            "Operación bloqueada: no estamos en "
            "la base de datos de pruebas."
        )