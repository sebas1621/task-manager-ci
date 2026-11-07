"""FastAPI dependency providers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, SystemClock
from app.db.session import get_session
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.services.health_service import HealthService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

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


def get_clock() -> Clock:
    """Provide the system clock.

    Returns:
        A SystemClock instance.
    """
    return SystemClock()


def get_task_repository(session: SessionDep) -> TaskRepository:
    """Build a task repository bound to the request session.

    Args:
        session: Database session for the current request.

    Returns:
        A TaskRepository instance.
    """
    return TaskRepository(session)


def get_task_service(
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
    project_repository: Annotated[ProjectRepository, Depends(get_project_repository)],
    clock: Annotated[Clock, Depends(get_clock)],
) -> TaskService:
    """Build a task service around its collaborators.

    Args:
        task_repository: Task repository for the current request.
        project_repository: Project repository for the current request.
        clock: Time source.

    Returns:
        A TaskService instance.
    """
    return TaskService(task_repository, project_repository, clock)
