"""Unit tests for ``app.repositories.project_repository``."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository


@pytest.fixture
def session() -> MagicMock:
    """Provide a mocked SQLAlchemy session."""
    return MagicMock(spec=Session)


@pytest.fixture
def repository(session: MagicMock) -> ProjectRepository:
    """Provide a repository bound to the mocked session.

    Args:
        session: The mocked session.

    Returns:
        A ProjectRepository using the mock.
    """
    return ProjectRepository(session)


def _executed_select(session: MagicMock) -> Select:
    """Return the select statement passed to ``scalars`` or ``scalar``.

    Args:
        session: The mocked session that ran the query.

    Returns:
        The statement given to the session.
    """
    call = (
        session.scalars.call_args
        if session.scalars.called
        else session.scalar.call_args
    )
    statement = call.args[0]
    assert isinstance(statement, Select)
    return statement


def test_add_persists_commits_refreshes_in_order(
    repository: ProjectRepository, session: MagicMock
) -> None:
    """add() calls add, commit, refresh in that order."""
    project = Project(name="Alpha")

    repository.add(project)

    names = [call[0] for call in session.method_calls]
    assert names == ["add", "commit", "refresh"]
    session.add.assert_called_once_with(project)
    session.refresh.assert_called_once_with(project)


def test_add_returns_the_same_project(repository: ProjectRepository) -> None:
    """add() returns the instance it received."""
    project = Project(name="Alpha")

    assert repository.add(project) is project


def test_get_by_name_when_found_returns_project(
    repository: ProjectRepository, session: MagicMock
) -> None:
    """A matching row is returned."""
    project = Project(name="Alpha")
    session.scalar.return_value = project
    session.scalars.return_value.first.return_value = project

    assert repository.get_by_name("Alpha") is project


def test_get_by_name_when_missing_returns_none(
    repository: ProjectRepository, session: MagicMock
) -> None:
    """No row means None."""
    session.scalar.return_value = None
    session.scalars.return_value.first.return_value = None

    assert repository.get_by_name("Nope") is None


def test_get_by_name_builds_select_filtered_by_name(
    repository: ProjectRepository, session: MagicMock
) -> None:
    """The query filters on projects.name with the given value."""
    repository.get_by_name("Alpha")

    compiled = _executed_select(session).compile()
    assert "WHERE projects.name" in str(compiled)
    assert "Alpha" in compiled.params.values()


def test_list_all_returns_rows_as_list(
    repository: ProjectRepository, session: MagicMock
) -> None:
    """list_all returns the scalars as a list."""
    projects = [Project(name="A"), Project(name="B")]
    session.scalars.return_value.all.return_value = projects

    assert repository.list_all() == projects


def test_list_all_builds_select_ordered_by_id(
    repository: ProjectRepository, session: MagicMock
) -> None:
    """The query orders by projects.id."""
    repository.list_all()

    assert "ORDER BY projects.id" in str(_executed_select(session).compile())
