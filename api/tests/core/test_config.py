"""Unit tests for ``app.core.config``."""

import pytest
from pydantic import SecretStr, ValidationError
from sqlalchemy.engine import URL

from app.core.config import Settings, get_settings

REQUIRED_VARS = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "DB_HOST")


@pytest.mark.usefixtures("full_env")
def test_settings_with_required_env_reads_values() -> None:
    """Required variables are read from the environment."""
    settings = Settings()

    assert settings.postgres_user == "test-user"
    assert isinstance(settings.postgres_password, SecretStr)
    assert settings.postgres_password.get_secret_value() == "test-password"
    assert settings.postgres_db == "db"
    assert settings.db_host == "db-host"


@pytest.mark.usefixtures("full_env")
def test_settings_without_optional_env_uses_defaults() -> None:
    """DB_PORT and APP_NAME fall back to their defaults."""
    settings = Settings()

    assert settings.db_port == 5432
    assert settings.app_name == "Task Manager API"


@pytest.mark.usefixtures("full_env")
def test_settings_with_optional_env_overrides_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DB_PORT is parsed as int and APP_NAME can be overridden."""
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("APP_NAME", "Custom")

    settings = Settings()

    assert settings.db_port == 6543
    assert settings.app_name == "Custom"


@pytest.mark.parametrize("missing", REQUIRED_VARS)
def test_settings_missing_required_var_raises_validation_error(
    monkeypatch: pytest.MonkeyPatch, full_env: None, missing: str
) -> None:
    """Each required variable raises ValidationError when absent."""
    monkeypatch.delenv(missing)

    with pytest.raises(ValidationError):
        Settings()


def test_settings_config_does_not_read_env_file() -> None:
    """Settings must not load a .env file by itself."""
    assert Settings.model_config.get("env_file") is None


@pytest.mark.usefixtures("full_env")
def test_settings_database_url_returns_url_with_expected_fields() -> None:
    """The database URL is a SQLAlchemy URL with psycopg driver and fields."""
    settings = Settings()

    url = settings.database_url

    assert isinstance(url, URL)
    assert url.drivername == "postgresql+psycopg"
    assert url.username == "test-user"
    assert url.password == "test-password"
    assert url.host == "db-host"
    assert url.port == 5432
    assert url.database == "db"


def test_settings_database_url_with_special_password_preserves_it() -> None:
    """A password with reserved URL characters is kept exactly."""
    password = "p@ss:w/rd#?%"
    settings = Settings(
        postgres_user="test-user",
        postgres_password=password,
        postgres_db="db",
        db_host="db-host",
    )

    url = settings.database_url

    assert url.password == password
    assert url.host == "db-host"


@pytest.mark.usefixtures("full_env")
def test_settings_database_url_str_hides_password() -> None:
    """Rendering the URL as a string masks the password."""
    settings = Settings()

    assert "test-password" not in str(settings.database_url)


@pytest.mark.usefixtures("full_env")
def test_settings_repr_and_str_hide_password() -> None:
    """The password never appears in repr() or str()."""
    settings = Settings()

    assert "test-password" not in repr(settings)
    assert "test-password" not in str(settings)


@pytest.mark.usefixtures("full_env")
def test_get_settings_called_twice_returns_same_instance() -> None:
    """get_settings is cached."""
    first = get_settings()
    second = get_settings()

    assert isinstance(first, Settings)
    assert first is second
