"""Unit tests for ``app.services.project_service``."""

from typing import cast

import pytest

from app.core.exceptions import DuplicateProjectNameError
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate
from app.services.project_service import ProjectService


class FakeProjectRepository:
    """In-memory stand-in for ProjectRepository.

    Attributes:
        projects: Stored projects in insertion order.
    """

    def __init__(self) -> None:
        """Start with no stored projects."""
        self.projects: list[Project] = []

    def add(self, project: Project) -> Project:
        """Store a project and assign an id."""
        project.id = len(self.projects) + 1
        self.projects.append(project)
        return project

    def get_by_name(self, name: str) -> Project | None:
        """Find a stored project by exact name."""
        return next((p for p in self.projects if p.name == name), None)

    def list_all(self) -> list[Project]:
        """Return all stored projects."""
        return list(self.projects)


@pytest.fixture
def repository() -> FakeProjectRepository:
    """Provide an empty in-memory repository."""
    return FakeProjectRepository()


@pytest.fixture
def service(repository: FakeProjectRepository) -> ProjectService:
    """Provide a service backed by the fake repository.

    Args:
        repository: The in-memory repository.

    Returns:
        A ProjectService instance.
    """
    return ProjectService(cast(ProjectRepository, repository))


def test_create_project_with_new_name_returns_persisted_project(
    service: ProjectService, repository: FakeProjectRepository
) -> None:
    """A fresh name creates and stores the project."""
    project = service.create_project(ProjectCreate(name="Alpha", description="d"))

    assert project.name == "Alpha"
    assert project.description == "d"
    assert repository.projects == [project]


def test_create_project_without_description_stores_none(
    service: ProjectService,
) -> None:
    """Description defaults to None."""
    assert service.create_project(ProjectCreate(name="Alpha")).description is None


def test_create_project_with_existing_name_raises_duplicate_error(
    service: ProjectService, repository: FakeProjectRepository
) -> None:
    """A taken name is rejected and nothing else is stored."""
    service.create_project(ProjectCreate(name="Alpha"))

    with pytest.raises(DuplicateProjectNameError, match="Alpha"):
        service.create_project(ProjectCreate(name="Alpha"))

    assert len(repository.projects) == 1


def test_list_projects_returns_all_projects(service: ProjectService) -> None:
    """All stored projects are listed."""
    first = service.create_project(ProjectCreate(name="A"))
    second = service.create_project(ProjectCreate(name="B"))

    assert service.list_projects() == [first, second]


def test_list_projects_when_empty_returns_empty_list(
    service: ProjectService,
) -> None:
    """No projects yields an empty list."""
    assert service.list_projects() == []
