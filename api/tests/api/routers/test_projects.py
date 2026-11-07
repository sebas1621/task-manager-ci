"""Unit tests for ``app.api.routers.projects``."""

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_project_service
from app.core.config import Settings
from app.core.exceptions import DuplicateProjectNameError
from app.main import create_app
from app.models.project import Project
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService

CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


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


def _project(project_id: int, name: str, description: str | None = None) -> Project:
    """Build an in-memory project with every field set.

    Args:
        project_id: Identifier to assign.
        name: Project name.
        description: Optional description.

    Returns:
        A Project that was never persisted.
    """
    return Project(
        id=project_id,
        name=name,
        description=description,
        is_archived=False,
        created_at=CREATED_AT,
    )


@pytest.fixture
def service() -> MagicMock:
    """Provide a mocked ProjectService."""
    return MagicMock(spec=ProjectService)


@pytest.fixture
def client(service: MagicMock) -> Iterator[TestClient]:
    """Provide a TestClient whose project service is the mock.

    Args:
        service: The mocked project service to inject.

    Yields:
        A TestClient bound to an app with the dependency overridden.
    """
    app = create_app(_settings())
    app.dependency_overrides[get_project_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_project_with_valid_body_returns_201_and_project(
    client: TestClient, service: MagicMock
) -> None:
    """A valid body yields 201 and the serialized project."""
    service.create_project.return_value = _project(1, "Alpha", "First")

    response = client.post("/projects", json={"name": "Alpha", "description": "First"})

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "Alpha",
        "description": "First",
        "is_archived": False,
        "created_at": "2026-01-01T12:00:00Z",
    }


def test_create_project_passes_validated_data_to_service(
    client: TestClient, service: MagicMock
) -> None:
    """The service receives a stripped ProjectCreate."""
    service.create_project.return_value = _project(1, "Alpha")

    client.post("/projects", json={"name": "  Alpha  "})

    service.create_project.assert_called_once_with(ProjectCreate(name="Alpha"))


def test_create_project_with_duplicate_name_returns_409(
    client: TestClient, service: MagicMock
) -> None:
    """A duplicate name yields 409 with the error message."""
    service.create_project.side_effect = DuplicateProjectNameError("Alpha")

    response = client.post("/projects", json={"name": "Alpha"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Project with name 'Alpha' already exists"}


@pytest.mark.parametrize("body", [{"name": "   "}, {"name": ""}, {}])
def test_create_project_with_invalid_body_returns_422(
    client: TestClient, service: MagicMock, body: dict[str, str]
) -> None:
    """Blank or missing names are rejected before reaching the service."""
    response = client.post("/projects", json=body)

    assert response.status_code == 422
    service.create_project.assert_not_called()


def test_list_projects_returns_200_and_all_projects(
    client: TestClient, service: MagicMock
) -> None:
    """GET /projects returns the serialized list."""
    service.list_projects.return_value = [_project(1, "A"), _project(2, "B", "x")]

    response = client.get("/projects")

    assert response.status_code == 200
    body = response.json()
    assert [item["name"] for item in body] == ["A", "B"]
    assert body[1]["description"] == "x"


def test_list_projects_when_empty_returns_empty_list(
    client: TestClient, service: MagicMock
) -> None:
    """No projects yields an empty JSON array."""
    service.list_projects.return_value = []

    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json() == []
