"""FastAPI dependency providers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.project_repository import ProjectRepository
from app.services.health_service import HealthService
from app.services.project_service import ProjectService

SessionDep = Annotated[Session, Depends(get_session)]


def get_health_service(session: SessionDep) -> HealthService:
    """Build a health service bound to the request session.

    Args:
        session: Database session for the current request.

    Returns:
        A HealthService instance.
    """
    return HealthService(session)


def get_project_repository(session: SessionDep) -> ProjectRepository:
    """Build a project repository bound to the request session.

    Args:
        session: Database session for the current request.

    Returns:
        A ProjectRepository instance.
    """
    return ProjectRepository(session)


def get_project_service(
    repository: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> ProjectService:
    """Build a project service around a repository.

    Args:
        repository: Project repository for the current request.

    Returns:
        A ProjectService instance.
    """
    return ProjectService(repository)
