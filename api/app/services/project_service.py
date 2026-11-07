"""Business rules for projects."""

from app.core.exceptions import DuplicateProjectNameError
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:
    """Creates and lists projects."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Bind the service to a repository.

        Args:
            repository: Repository used for persistence.
        """
        self._repository = repository

    def create_project(self, data: ProjectCreate) -> Project:
        """Create a project with a unique name.

        Args:
            data: Validated creation payload.

        Returns:
            The persisted project.

        Raises:
            DuplicateProjectNameError: If the name is already taken.
        """
        if self._repository.get_by_name(data.name) is not None:
            raise DuplicateProjectNameError(data.name)
        return self._repository.add(
            Project(name=data.name, description=data.description)
        )

    def list_projects(self) -> list[Project]:
        """List all projects.

        Returns:
            Every stored project.
        """
        return self._repository.list_all()
