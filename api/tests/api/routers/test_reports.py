"""Unit tests for ``app.api.routers.reports``."""

from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_report_service
from app.core.config import Settings
from app.core.exceptions import ProjectNotFoundError
from app.main import create_app
from app.schemas.report import ProjectSummary, StatusCounts
from app.services.report_service import ReportService


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
    """Provide a mocked ReportService."""
    return MagicMock(spec=ReportService)


@pytest.fixture
def client(service: MagicMock) -> Iterator[TestClient]:
    """Provide a TestClient whose report service is the mock.

    Args:
        service: The mocked report service to inject.

    Yields:
        A TestClient bound to an app with the dependency overridden.
    """
    app = create_app(_settings())
    app.dependency_overrides[get_report_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_project_summary_returns_200_and_service_body(
    client: TestClient, service: MagicMock
) -> None:
    """The service result is serialized as the response body."""
    service.project_summary.return_value = ProjectSummary(
        project_id=5,
        total_tasks=3,
        status_counts=StatusCounts(todo=1, in_progress=1, done=1),
        completion_percentage=33.33,
        overdue_tasks=1,
    )

    response = client.get("/reports/projects/5/summary")

    assert response.status_code == 200
    assert response.json() == {
        "project_id": 5,
        "total_tasks": 3,
        "status_counts": {"todo": 1, "in_progress": 1, "done": 1},
        "completion_percentage": 33.33,
        "overdue_tasks": 1,
    }
    service.project_summary.assert_called_once_with(5)


def test_get_project_summary_with_missing_project_returns_404(
    client: TestClient, service: MagicMock
) -> None:
    """A missing project is mapped to the standard 404 body."""
    service.project_summary.side_effect = ProjectNotFoundError(9)

    response = client.get("/reports/projects/9/summary")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project 9 not found"}


def test_get_project_summary_with_non_integer_id_returns_422(
    client: TestClient, service: MagicMock
) -> None:
    """A non-integer project id fails validation before the service runs."""
    response = client.get("/reports/projects/abc/summary")

    assert response.status_code == 422
    service.project_summary.assert_not_called()
