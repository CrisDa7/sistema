"""Pruebas de seguridad de configuración y arranque."""

import os
import pytest

from app.config import Config, ProductionConfig
from app import create_app
from tests.test_config import TestConfig


def test_config_secret_key_from_env_or_generated():
    """Verifica que SECRET_KEY se obtenga de entorno o se genere aleatorio."""
    # Config por sí sola no tiene SECRET_KEY (se genera en create_app)
    config = Config()
    assert config.SECRET_KEY is None

    # Pero create_app lo genera
    app = create_app(Config)
    assert app.config["SECRET_KEY"] is not None
    assert len(app.config["SECRET_KEY"]) >= 32
    # Verificar que no sea el valor inseguro anterior
    assert app.config["SECRET_KEY"] != "active-gym-dev-secret-key"


def test_production_config_requires_secret_key_from_env():
    """Verifica que ProductionConfig requiere SECRET_KEY de entorno."""
    # ProductionConfig por sí sola sin SECRET_KEY tiene None
    config = ProductionConfig()
    assert config.SECRET_KEY is None

    # ProductionConfig usa SECRET_KEY de entorno si está disponible
    os.environ["SECRET_KEY"] = "production-secret-key"
    config = ProductionConfig()
    # ProductionConfig no asigna SECRET_KEY dinámicamente, create_app lo hace
    assert config.SECRET_KEY is None
    os.environ.pop("SECRET_KEY", None)


def test_production_app_fails_without_secret_key():
    """Verifica que app con ProductionConfig falle sin SECRET_KEY."""
    # Sin SECRET_KEY, debe lanzar RuntimeError
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(ProductionConfig)

    # Con SECRET_KEY, debe funcionar
    os.environ["SECRET_KEY"] = "production-secret-key"
    app = create_app(ProductionConfig)
    assert app.config["SECRET_KEY"] == "production-secret-key"
    os.environ.pop("SECRET_KEY", None)


def test_production_config_secure_cookies():
    """Verifica que ProductionConfig tenga cookies seguras."""
    os.environ["SECRET_KEY"] = "test-secret"
    config = ProductionConfig()

    assert config.SESSION_COOKIE_SECURE is True
    assert config.SESSION_COOKIE_SAMESITE == "Strict"
    assert config.SESSION_COOKIE_HTTPONLY is True

    os.environ.pop("SECRET_KEY", None)


def test_development_config_insecure_cookies():
    """Verifica que Config de desarrollo tenga cookies compatibles con HTTP."""
    config = Config()

    assert config.SESSION_COOKIE_SECURE is False
    assert config.SESSION_COOKIE_SAMESITE == "Lax"
    assert config.SESSION_COOKIE_HTTPONLY is True


def test_app_with_test_config_uses_test_database():
    """Verifica que la app con TestConfig use la base de pruebas."""
    app = create_app(TestConfig)

    with app.app_context():
        from sqlalchemy import text
        from app.extensions import db

        db_name = db.session.execute(text("SELECT current_database()")).scalar_one()
        assert db_name == "active_gym_test_db"


def test_test_config_secret_key_generated():
    """Verifica que TestConfig genere SECRET_KEY aleatorio en create_app."""
    # TestConfig por sí sola no tiene SECRET_KEY (se genera en create_app)
    config = TestConfig()
    assert config.SECRET_KEY is None

    # Pero create_app lo genera
    app = create_app(TestConfig)
    assert app.config["SECRET_KEY"] is not None
    assert len(app.config["SECRET_KEY"]) >= 32


def test_app_with_default_config_uses_dev_cookies():
    """Verifica que la app con Config por defecto use cookies de desarrollo."""
    from app.config import Config

    app = create_app(Config)

    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SECRET_KEY"] is not None
    assert len(app.config["SECRET_KEY"]) >= 32
