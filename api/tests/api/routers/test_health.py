"""Unit tests for ``app.api.routers.health``."""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_health_service
from app.core.config import Settings
from app.main import create_app
from app.services.health_service import HealthService


def _settings() -> Settings:
    """Build explicit settings with fake values.

    Returns:
        A Settings instance that needs no environment.
    """
    return Settings(
        postgres_user="test-user",
        postgres_password="test-password",
        postgres_db="db",
        db_host="db-host",
    )


@pytest.fixture
def service() -> MagicMock:
    """Provide a mocked HealthService."""
    return MagicMock(spec=HealthService)


@pytest.fixture
def client(service: MagicMock) -> Iterator[TestClient]:
    """Provide a TestClient whose health service is the mock.

    Args:
        service: The mocked health service to inject.

    Yields:
        A TestClient bound to an app with the dependency overridden.
    """
    app = create_app(_settings())
    app.dependency_overrides[get_health_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_health_when_database_available_returns_200_ok(
    client: TestClient, service: MagicMock
) -> None:
    """A reachable database yields 200 and the ok payload."""
    service.is_database_available.return_value = True

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_get_health_when_database_unavailable_returns_503_error(
    client: TestClient, service: MagicMock
) -> None:
    """An unreachable database yields 503 and the error payload."""
    service.is_database_available.return_value = False

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_get_health_calls_service_once(client: TestClient, service: MagicMock) -> None:
    """The endpoint checks the database exactly once per request."""
    service.is_database_available.return_value = True

    client.get("/health")

    service.is_database_available.assert_called_once_with()
