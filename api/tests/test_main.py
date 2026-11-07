"""Unit tests for ``app.main``."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def _settings(app_name: str = "Test App") -> Settings:
    """Build explicit settings so no environment is needed.

    Args:
        app_name: Application name to configure.

    Returns:
        A Settings instance with fake values.
    """
    return Settings(
        postgres_user="test-user",
        postgres_password="test-password",
        postgres_db="db",
        db_host="db-host",
        app_name=app_name,
    )


def test_create_app_with_settings_returns_app_titled_with_app_name() -> None:
    """The FastAPI title equals the configured APP_NAME."""
    app = create_app(_settings("Test App"))

    assert isinstance(app, FastAPI)
    assert app.title == "Test App"


def test_create_app_without_argument_uses_environment_settings(
    monkeypatch: pytest.MonkeyPatch, full_env: None
) -> None:
    """With no argument, settings come from the environment."""
    monkeypatch.setenv("APP_NAME", "Env App")

    app = create_app()

    assert app.title == "Env App"


def test_create_app_openapi_endpoint_returns_schema_with_title() -> None:
    """/openapi.json is served with the app name as title."""
    client = TestClient(create_app(_settings("Test App")))

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Test App"


def test_create_app_registers_health_route() -> None:
    """The /health route is part of the application."""
    app = create_app(_settings())

    paths = app.openapi()["paths"]

    assert "/health" in paths
