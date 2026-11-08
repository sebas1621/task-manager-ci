"""Unit tests for ``app.schemas.task``."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskRead, TaskStatusUpdate, is_overdue

TODAY = date(2026, 11, 7)
CREATED_AT = datetime(2026, 11, 1, 8, 0, tzinfo=UTC)


def _task(
    due_date: date | None = None,
    status: TaskStatus = TaskStatus.TODO,
    completed_at: datetime | None = None,
) -> Task:
    """Build an in-memory task with every field set.

    Args:
        due_date: Optional due date.
        status: Task status.
        completed_at: Optional completion timestamp.

    Returns:
        A Task that was never persisted.
    """
    return Task(
        id=4,
        project_id=2,
        title="Write",
        description="desc",
        status=status,
        priority=TaskPriority.HIGH,
        due_date=due_date,
        created_at=CREATED_AT,
        completed_at=completed_at,
    )


def test_task_create_with_only_required_fields_applies_defaults() -> None:
    """Optional fields default to None and medium priority."""
    data = TaskCreate(project_id=1, title="Write")

    assert data.description is None
    assert data.priority == TaskPriority.MEDIUM
    assert data.due_date is None


def test_task_create_with_padded_title_strips_it() -> None:
    """Surrounding whitespace is removed from the title."""
    assert TaskCreate(project_id=1, title="  Write  ").title == "Write"


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_task_create_with_blank_title_raises(title: str) -> None:
    """Blank titles are rejected."""
    with pytest.raises(ValidationError):
        TaskCreate(project_id=1, title=title)


def test_task_create_with_title_of_200_chars_is_valid() -> None:
    """200 characters is the maximum accepted length."""
    assert len(TaskCreate(project_id=1, title="a" * 200).title) == 200


def test_task_create_with_title_over_200_chars_raises() -> None:
    """201 characters is rejected."""
    with pytest.raises(ValidationError):
        TaskCreate(project_id=1, title="a" * 201)


def test_task_create_without_project_id_raises() -> None:
    """project_id is required."""
    with pytest.raises(ValidationError):
        TaskCreate.model_validate({"title": "Write"})


def test_task_create_with_invalid_priority_raises() -> None:
    """Unknown priorities are rejected."""
    with pytest.raises(ValidationError):
        TaskCreate.model_validate(
            {"project_id": 1, "title": "Write", "priority": "urgent"}
        )


def test_task_create_with_all_fields_keeps_them() -> None:
    """Every given field is preserved."""
    data = TaskCreate(
        project_id=3,
        title="Write",
        description="d",
        priority=TaskPriority.LOW,
        due_date=date(2026, 12, 1),
    )

    assert data.project_id == 3
    assert data.description == "d"
    assert data.priority == TaskPriority.LOW
    assert data.due_date == date(2026, 12, 1)


def test_task_status_update_with_valid_status_parses_enum() -> None:
    """A valid string becomes a TaskStatus."""
    assert TaskStatusUpdate.model_validate({"status": "done"}).status == TaskStatus.DONE


def test_task_status_update_with_invalid_status_raises() -> None:
    """Unknown statuses are rejected."""
    with pytest.raises(ValidationError):
        TaskStatusUpdate.model_validate({"status": "archived"})


def test_task_read_from_task_copies_all_fields() -> None:
    """from_task maps every ORM field."""
    completed = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)
    task = _task(date(2026, 11, 20), TaskStatus.DONE, completed)

    result = TaskRead.from_task(task, TODAY)

    assert result.id == 4
    assert result.project_id == 2
    assert result.title == "Write"
    assert result.description == "desc"
    assert result.status == TaskStatus.DONE
    assert result.priority == TaskPriority.HIGH
    assert result.due_date == date(2026, 11, 20)
    assert result.created_at == CREATED_AT
    assert result.completed_at == completed


@pytest.mark.parametrize(
    ("due_date", "status", "expected"),
    [
        (None, TaskStatus.TODO, False),
        (TODAY, TaskStatus.TODO, False),
        (date(2026, 11, 6), TaskStatus.TODO, True),
        (date(2026, 11, 6), TaskStatus.IN_PROGRESS, True),
        (date(2026, 11, 6), TaskStatus.DONE, False),
        (date(2026, 11, 8), TaskStatus.TODO, False),
    ],
)
def test_task_read_from_task_computes_is_overdue(
    due_date: date | None, status: TaskStatus, expected: bool
) -> None:
    """is_overdue is true only for past due dates on unfinished tasks."""
    completed = CREATED_AT if status == TaskStatus.DONE else None

    result = TaskRead.from_task(_task(due_date, status, completed), TODAY)

    assert result.is_overdue is expected


@pytest.mark.parametrize(
    ("due_date", "status", "expected"),
    [
        (None, TaskStatus.TODO, False),
        (date(2026, 11, 6), TaskStatus.TODO, True),
        (date(2026, 11, 6), TaskStatus.IN_PROGRESS, True),
        (date(2026, 11, 6), TaskStatus.DONE, False),
        (TODAY, TaskStatus.TODO, False),
        (date(2026, 11, 8), TaskStatus.TODO, False),
    ],
)
def test_is_overdue_with_due_date_and_status_returns_expected(
    due_date: date | None, status: TaskStatus, expected: bool
) -> None:
    """Only past due dates on unfinished tasks are overdue."""
    task = _task(due_date, status)

    assert is_overdue(task, TODAY) is expected
