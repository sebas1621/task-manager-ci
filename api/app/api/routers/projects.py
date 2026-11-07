"""Projects router."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_project_service
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"description": "Name already exists"}},
)
def create_project(
    data: ProjectCreate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Create a project.

    Args:
        data: Validated creation payload.
        service: Project service.

    Returns:
        The created project.
    """
    return ProjectRead.model_validate(service.create_project(data))


@router.get("", response_model=list[ProjectRead])
def list_projects(
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ProjectRead]:
    """List all projects.

    Args:
        service: Project service.

    Returns:
        Every project ordered by id.
    """
    return [ProjectRead.model_validate(p) for p in service.list_projects()]
