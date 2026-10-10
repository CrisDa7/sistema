"""Pruebas del comando CLI de creación del primer administrador."""

import pytest
from click.testing import CliRunner

from app import create_app
from app.extensions import db
from app.models.admin import Admin, AdminSession
from tests.db_safety import ensure_test_database
from tests.test_config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        ensure_test_database()
        db.session.execute(db.delete(AdminSession))
        db.session.execute(db.delete(Admin))
        db.session.commit()
        yield app

    with app.app_context():
        ensure_test_database()
        db.session.execute(db.delete(AdminSession))
        db.session.execute(db.delete(Admin))
        db.session.commit()


def test_create_admin_command_creates_single_admin_in_test_database(app):
    runner = CliRunner()

    with app.app_context():
        ensure_test_database()

    result = runner.invoke(
        app.cli,
        ["create-admin"],
        input="activegym_admin\nStrongPass!123\nStrongPass!123\n",
    )

    assert result.exit_code == 0, result.output
    assert "Administrador creado correctamente: activegym_admin" in result.output

    with app.app_context():
        ensure_test_database()
        admin = db.session.query(Admin).filter_by(username="activegym_admin").one()
        assert admin.username == "activegym_admin"
        assert admin.password_hash != "StrongPass!123"


def test_create_admin_command_rejects_duplicate_username(app):
    runner = CliRunner()

    with app.app_context():
        ensure_test_database()
        db.session.execute(db.insert(Admin).values(username="activegym_admin", password_hash="hash"))
        db.session.commit()

    result = runner.invoke(
        app.cli,
        ["create-admin"],
        input="activegym_admin\nStrongPass!123\nStrongPass!123\n",
    )

    assert result.exit_code != 0
    assert "ya existe" in result.output.lower()


def test_create_admin_command_rejects_wrong_database(app, monkeypatch):
    runner = CliRunner()
    original_execute = db.session.execute

    def fake_execute(statement, *args, **kwargs):
        statement_text = str(statement).lower()
        if "current_database" in statement_text:
            class FakeScalarResult:
                def scalar_one(self):
                    return "other_db"

            return FakeScalarResult()
        return original_execute(statement, *args, **kwargs)

    monkeypatch.setattr(db.session, "execute", fake_execute)

    result = runner.invoke(
        app.cli,
        ["create-admin"],
        input="activegym_admin\nStrongPass!123\nStrongPass!123\n",
    )

    assert result.exit_code != 0
    assert "Operación bloqueada" in result.output
