"""Pruebas de seguridad de la base de datos."""

import pytest

from app import create_app
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig


def test_ensure_test_database_accepts_test_database():
    """Permite operar en la base de pruebas."""

    app = create_app(TestConfig)

    with app.app_context():
        assert ensure_test_database() is None


def test_ensure_test_database_rejects_wrong_database():
    """Rechaza una base distinta de la permitida."""

    from unittest.mock import patch

    app = create_app(TestConfig)

    with app.app_context():
        with patch(
            "tests.db_safety.db.session.execute"
        ) as mocked_execute:
            mocked_execute.return_value.scalar_one.return_value = (
                "active_gym_db"
            )

            with pytest.raises(
                RuntimeError,
                match="Operación bloqueada",
            ):
                ensure_test_database()