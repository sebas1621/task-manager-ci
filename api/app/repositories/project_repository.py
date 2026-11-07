"""Persistence queries for projects."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    """Encapsulates all SQLAlchemy access for projects."""

    def __init__(self, session: Session) -> None:
        """Bind the repository to a session.

        Args:
            session: Database session used for every query.
        """
        self._session = session

    def add(self, project: Project) -> Project:
        """Persist a project and reload its database-generated fields.

        Args:
            project: The project to store.

        Returns:
            The same project, refreshed after the commit.
        """
        self._session.add(project)
        self._session.commit()
        self._session.refresh(project)
        return project

    def get_by_id(self, project_id: int) -> Project | None:
        """Find a project by primary key.

        Args:
            project_id: The project id.

        Returns:
            The matching project, or None.
        """
        return self._session.get(Project, project_id)

    def get_by_name(self, name: str) -> Project | None:
        """Find a project by exact name.

        Args:
            name: The project name.

        Returns:
            The matching project, or None.
        """
        return self._session.scalar(select(Project).where(Project.name == name))

    def list_all(self) -> list[Project]:
        """List all projects ordered by id.

        Returns:
            Every stored project.
        """
        statement = select(Project).order_by(Project.id)
        return list(self._session.scalars(statement).all())
