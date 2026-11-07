"""Unit tests for ``app.api.deps``."""

from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.api.deps import (
    get_health_service,
    get_project_repository,
    get_project_service,
)
from app.repositories.project_repository import ProjectRepository
from app.services.health_service import HealthService
from app.services.project_service import ProjectService


def test_get_health_service_with_session_returns_bound_service() -> None:
    """The provider builds a HealthService around the given session."""
    session = MagicMock(spec=Session)

    service = get_health_service(session)

    assert isinstance(service, HealthService)
    service.is_database_available()
    session.execute.assert_called_once()


def test_get_project_repository_with_session_returns_bound_repository() -> None:
    """The provider builds a ProjectRepository around the given session."""
    session = MagicMock(spec=Session)

    repository = get_project_repository(session)

    assert isinstance(repository, ProjectRepository)
    repository.list_all()
    session.scalars.assert_called_once()


def test_get_project_service_with_repository_returns_service() -> None:
    """The provider builds a ProjectService around the repository."""
    repository = MagicMock(spec=ProjectRepository)
    repository.list_all.return_value = []

    service = get_project_service(repository)

    assert isinstance(service, ProjectService)
    assert service.list_projects() == []
    repository.list_all.assert_called_once_with()
