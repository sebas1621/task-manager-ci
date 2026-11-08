"""Unit tests for ``app.services.report_service``."""

from datetime import UTC, date, datetime
from typing import cast

import pytest

from app.core.exceptions import ProjectNotFoundError
from app.models.enums import TaskPriority, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.report import StatusCounts
from app.services.report_service import ReportService

TODAY = date(2026, 11, 7)
YESTERDAY = date(2026, 11, 6)
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


class FakeClock:
    """Clock frozen at a known instant."""

    def today(self) -> date:
        """Return the fixed date."""
        return TODAY

    def now(self) -> datetime:
        """Return the fixed instant."""
        return NOW


class FakeProjectRepository:
    """In-memory stand-in for ProjectRepository.

    Attributes:
        projects: Projects keyed by id.
    """

    def __init__(self) -> None:
        """Start with an active project 1 and an archived project 2."""
        self.projects: dict[int, Project] = {
            1: Project(id=1, name="P1", is_archived=False),
            2: Project(id=2, name="P2", is_archived=True),
        }

    def get_by_id(self, project_id: int) -> Project | None:
        """Find a project by id."""
        return self.projects.get(project_id)


class FakeTaskRepository:
    """In-memory stand-in for TaskRepository.

    Attributes:
        tasks: Tasks returned by ``list``.
        list_calls: Keyword arguments received by each ``list`` call.
    """

    def __init__(self) -> None:
        """Start empty."""
        self.tasks: list[Task] = []
        self.list_calls: list[dict[str, object]] = []

    def list(
        self,
        project_id: int | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> list[Task]:
        """Record the filters and return the stored tasks."""
        self.list_calls.append(
            {"project_id": project_id, "status": status, "priority": priority}
        )
        return list(self.tasks)


@pytest.fixture
def task_repo() -> FakeTaskRepository:
    """Provide an empty fake task repository."""
    return FakeTaskRepository()


@pytest.fixture
def service(task_repo: FakeTaskRepository) -> ReportService:
    """Build the service under test with fakes.

    Args:
        task_repo: Fake task repository.

    Returns:
        A ReportService wired to the fakes and a frozen clock.
    """
    return ReportService(
        cast(TaskRepository, task_repo),
        cast(ProjectRepository, FakeProjectRepository()),
        FakeClock(),
    )


def _task(status: TaskStatus = TaskStatus.TODO, due_date: date | None = None) -> Task:
    """Build an in-memory task.

    Args:
        status: Task status.
        due_date: Optional due date.

    Returns:
        A Task instance.
    """
    return Task(
        project_id=1,
        title="Write",
        status=status,
        priority=TaskPriority.MEDIUM,
        due_date=due_date,
    )


def test_project_summary_with_missing_project_raises_and_skips_tasks(
    service: ReportService, task_repo: FakeTaskRepository
) -> None:
    """An unknown project raises and the task repository is not queried."""
    with pytest.raises(ProjectNotFoundError):
        service.project_summary(99)

    assert task_repo.list_calls == []


def test_project_summary_without_tasks_returns_zeros(service: ReportService) -> None:
    """An empty project yields zero everywhere without dividing by zero."""
    result = service.project_summary(1)

    assert result.project_id == 1
    assert result.total_tasks == 0
    assert result.status_counts == StatusCounts(todo=0, in_progress=0, done=0)
    assert result.completion_percentage == 0.0
    assert result.overdue_tasks == 0


def test_project_summary_with_mixed_tasks_counts_each_status(
    service: ReportService, task_repo: FakeTaskRepository
) -> None:
    """Totals and per-status counts match the stored tasks."""
    task_repo.tasks = [
        _task(TaskStatus.TODO),
        _task(TaskStatus.TODO),
        _task(TaskStatus.IN_PROGRESS),
        _task(TaskStatus.DONE),
    ]

    result = service.project_summary(1)

    assert result.total_tasks == 4
    assert result.status_counts == StatusCounts(todo=2, in_progress=1, done=1)
    assert result.completion_percentage == 25.0


@pytest.mark.parametrize(
    ("done", "total", "expected"),
    [(0, 3, 0.0), (1, 3, 33.33), (2, 3, 66.67), (3, 3, 100.0)],
)
def test_project_summary_completion_percentage_is_rounded_to_two_decimals(
    service: ReportService,
    task_repo: FakeTaskRepository,
    done: int,
    total: int,
    expected: float,
) -> None:
    """Completion is done/total*100 rounded to two decimals."""
    task_repo.tasks = [_task(TaskStatus.DONE) for _ in range(done)] + [
        _task(TaskStatus.TODO) for _ in range(total - done)
    ]

    result = service.project_summary(1)

    assert result.completion_percentage == expected


@pytest.mark.parametrize(
    ("status", "due_date", "expected_overdue"),
    [
        (TaskStatus.TODO, YESTERDAY, 1),
        (TaskStatus.IN_PROGRESS, YESTERDAY, 1),
        (TaskStatus.DONE, YESTERDAY, 0),
        (TaskStatus.TODO, TODAY, 0),
        (TaskStatus.TODO, None, 0),
    ],
)
def test_project_summary_overdue_count_follows_clock_today(
    service: ReportService,
    task_repo: FakeTaskRepository,
    status: TaskStatus,
    due_date: date | None,
    expected_overdue: int,
) -> None:
    """Only past-due tasks that are not done count as overdue."""
    task_repo.tasks = [_task(status, due_date)]

    result = service.project_summary(1)

    assert result.overdue_tasks == expected_overdue


def test_project_summary_filters_tasks_by_project_only(
    service: ReportService, task_repo: FakeTaskRepository
) -> None:
    """The task repository is queried once, filtered by project id only."""
    service.project_summary(1)

    assert task_repo.list_calls == [{"project_id": 1, "status": None, "priority": None}]


def test_project_summary_with_archived_project_still_returns_summary(
    service: ReportService, task_repo: FakeTaskRepository
) -> None:
    """Archived projects can still be reported on."""
    task_repo.tasks = [_task(TaskStatus.DONE)]

    result = service.project_summary(2)

    assert result.project_id == 2
    assert result.total_tasks == 1
    assert result.completion_percentage == 100.0
