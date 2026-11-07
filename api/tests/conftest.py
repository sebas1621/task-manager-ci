"""Shared pytest fixtures for the whole test suite."""

from collections.abc import Iterator

import pytest

from app.core.config import get_settings

ENV_VARS = (
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "DB_HOST",
    "DB_PORT",
    "APP_NAME",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove every settings variable and reset the settings cache.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Yields:
        None, once the environment is isolated from the host.
    """
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def full_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set all required environment variables with fake values."""
    monkeypatch.setenv("POSTGRES_USER", "test-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test-password")
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("DB_HOST", "db-host")
