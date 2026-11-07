"""Unit tests for ``app.repositories.task_repository``."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.repositories.task_repository import TaskRepository


@pytest.fixture
def session() -> MagicMock:
    """Provide a mocked SQLAlchemy session."""
    return MagicMock(spec=Session)


@pytest.fixture
def repository(session: MagicMock) -> TaskRepository:
    """Provide a repository bound to the mocked session.

    Args:
        session: The mocked session.

    Returns:
        A TaskRepository using the mock.
    """
    return TaskRepository(session)


def _compiled_sql(session: MagicMock) -> str:
    """Compile the select statement passed to ``session.scalars``.

    Args:
        session: The mocked session that ran the query.

    Returns:
        The SQL text of the statement.
    """
    statement = session.scalars.call_args.args[0]
    assert isinstance(statement, Select)
    return str(statement.compile())


def _where_clause(sql: str) -> str:
    """Extract the WHERE section of a compiled statement.

    Args:
        sql: The compiled SQL text.

    Returns:
        The text between WHERE and ORDER BY.
    """
    return sql.split("WHERE", 1)[1].split("ORDER BY")[0]


def test_add_persists_commits_refreshes_in_order(
    repository: TaskRepository, session: MagicMock
) -> None:
    """add() calls add, commit, refresh in that order."""
    task = Task(title="Write")

    repository.add(task)

    assert [call[0] for call in session.method_calls] == ["add", "commit", "refresh"]
    session.add.assert_called_once_with(task)
    session.refresh.assert_called_once_with(task)


def test_add_returns_the_same_task(repository: TaskRepository) -> None:
    """add() returns the instance it received."""
    task = Task(title="Write")

    assert repository.add(task) is task


def test_get_by_id_when_found_returns_task(
    repository: TaskRepository, session: MagicMock
) -> None:
    """get_by_id delegates to session.get."""
    task = Task(title="Write")
    session.get.return_value = task

    assert repository.get_by_id(1) is task
    session.get.assert_called_once_with(Task, 1)


def test_get_by_id_when_missing_returns_none(
    repository: TaskRepository, session: MagicMock
) -> None:
    """No row means None."""
    session.get.return_value = None

    assert repository.get_by_id(1) is None


def test_list_returns_rows_as_list(
    repository: TaskRepository, session: MagicMock
) -> None:
    """List returns the scalars as a list."""
    tasks = [Task(title="A"), Task(title="B")]
    session.scalars.return_value.all.return_value = tasks

    assert repository.list() == tasks


def test_list_without_filters_has_no_where_and_orders_by_id(
    repository: TaskRepository, session: MagicMock
) -> None:
    """With no filters only the ordering is applied."""
    repository.list()

    sql = _compiled_sql(session)
    assert "WHERE" not in sql
    assert "ORDER BY tasks.id" in sql


@pytest.mark.parametrize(
    ("kwargs", "present", "absent"),
    [
        (
            {"project_id": 1},
            ["tasks.project_id ="],
            ["tasks.status =", "tasks.priority ="],
        ),
        (
            {"status": TaskStatus.DONE},
            ["tasks.status ="],
            ["tasks.project_id =", "tasks.priority ="],
        ),
        (
            {"priority": TaskPriority.HIGH},
            ["tasks.priority ="],
            ["tasks.project_id =", "tasks.status ="],
        ),
    ],
)
def test_list_with_single_filter_applies_only_that_filter(
    repository: TaskRepository,
    session: MagicMock,
    kwargs: dict[str, object],
    present: list[str],
    absent: list[str],
) -> None:
    """Only the given filter appears in the WHERE clause."""
    repository.list(**kwargs)  # type: ignore[arg-type]

    sql = _compiled_sql(session)
    where = _where_clause(sql)
    for fragment in present:
        assert fragment in where
    for fragment in absent:
        assert fragment not in where
    assert "ORDER BY tasks.id" in sql


def test_list_with_all_filters_applies_all_of_them(
    repository: TaskRepository, session: MagicMock
) -> None:
    """Every filter is combined in the WHERE clause."""
    repository.list(project_id=1, status=TaskStatus.TODO, priority=TaskPriority.LOW)

    where = _where_clause(_compiled_sql(session))
    assert "tasks.project_id =" in where
    assert "tasks.status =" in where
    assert "tasks.priority =" in where


def test_save_commits_refreshes_and_returns_task(
    repository: TaskRepository, session: MagicMock
) -> None:
    """save() commits then refreshes, without adding."""
    task = Task(title="Write")

    result = repository.save(task)

    assert result is task
    assert [call[0] for call in session.method_calls] == ["commit", "refresh"]
    session.refresh.assert_called_once_with(task)


def test_delete_deletes_then_commits(
    repository: TaskRepository, session: MagicMock
) -> None:
    """delete() removes the row and commits."""
    task = Task(title="Write")

    repository.delete(task)

    assert [call[0] for call in session.method_calls] == ["delete", "commit"]
    session.delete.assert_called_once_with(task)
