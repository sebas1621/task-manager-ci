"""Unit tests for ``app.services.task_service``."""

from datetime import UTC, date, datetime
from typing import cast

import pytest

from app.core.exceptions import (
    ArchivedProjectError,
    PastDueDateError,
    ProjectNotFoundError,
    TaskNotFoundError,
)
from app.models.enums import TaskPriority, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate
from app.services.task_service import TaskService

TODAY = date(2026, 11, 7)
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
EARLIER = datetime(2026, 11, 6, 8, 0, tzinfo=UTC)


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
        """Start with no projects."""
        self.projects: dict[int, Project] = {}

    def add_project(self, project_id: int, is_archived: bool = False) -> None:
        """Register a project.

        Args:
            project_id: Identifier to store.
            is_archived: Whether the project is archived.
        """
        self.projects[project_id] = Project(
            id=project_id, name=f"P{project_id}", is_archived=is_archived
        )

    def get_by_id(self, project_id: int) -> Project | None:
        """Find a project by id."""
        return self.projects.get(project_id)


class FakeTaskRepository:
    """In-memory stand-in for TaskRepository.

    Attributes:
        tasks: Tasks keyed by id.
        list_calls: Keyword arguments received by each ``list`` call.
        saved: Tasks passed to ``save``.
        deleted: Tasks passed to ``delete``.
    """

    def __init__(self) -> None:
        """Start empty."""
        self.tasks: dict[int, Task] = {}
        self.list_calls: list[dict[str, object]] = []
        self.saved: list[Task] = []
        self.deleted: list[Task] = []

    def add(self, task: Task) -> Task:
        """Store a task, assigning id and created_at like a refresh would."""
        task.id = len(self.tasks) + 1
        task.created_at = EARLIER
        self.tasks[task.id] = task
        return task

    def get_by_id(self, task_id: int) -> Task | None:
        """Find a task by id."""
        return self.tasks.get(task_id)

    def list(
        self,
        project_id: int | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> list[Task]:
        """Record the filters and return every stored task."""
        self.list_calls.append(
            {"project_id": project_id, "status": status, "priority": priority}
        )
        return list(self.tasks.values())

    def save(self, task: Task) -> Task:
        """Record a save."""
        self.saved.append(task)
        return task

    def delete(self, task: Task) -> None:
        """Remove a task and record it."""
        self.deleted.append(task)
        self.tasks.pop(task.id, None)


@pytest.fixture
def task_repo() -> FakeTaskRepository:
    """Provide an empty fake task repository."""
    return FakeTaskRepository()


@pytest.fixture
def project_repo() -> FakeProjectRepository:
    """Provide a fake project repository holding active project 1."""
    repo = FakeProjectRepository()
    repo.add_project(1)
    return repo


@pytest.fixture
def service(
    task_repo: FakeTaskRepository, project_repo: FakeProjectRepository
) -> TaskService:
    """Build the service under test with fakes.

    Args:
        task_repo: Fake task repository.
        project_repo: Fake project repository.

    Returns:
        A TaskService wired to the fakes and a frozen clock.
    """
    return TaskService(
        cast(TaskRepository, task_repo),
        cast(ProjectRepository, project_repo),
        FakeClock(),
    )


def _stored_task(
    repo: FakeTaskRepository,
    status: TaskStatus = TaskStatus.TODO,
    completed_at: datetime | None = None,
    due_date: date | None = None,
) -> Task:
    """Add a task to the fake repository.

    Args:
        repo: Fake task repository.
        status: Task status.
        completed_at: Completion timestamp.
        due_date: Optional due date.

    Returns:
        The stored task.
    """
    return repo.add(
        Task(
            project_id=1,
            title="Write",
            status=status,
            priority=TaskPriority.MEDIUM,
            due_date=due_date,
            completed_at=completed_at,
        )
    )


def test_create_task_with_valid_data_returns_task_read(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """A valid payload is stored as a todo task and returned."""
    data = TaskCreate(
        project_id=1,
        title="Write",
        description="d",
        priority=TaskPriority.HIGH,
        due_date=date(2026, 11, 20),
    )

    result = service.create_task(data)

    stored = task_repo.tasks[1]
    assert stored.status == TaskStatus.TODO
    assert stored.completed_at is None
    assert stored.title == "Write"
    assert stored.description == "d"
    assert stored.priority == TaskPriority.HIGH
    assert stored.due_date == date(2026, 11, 20)
    assert result.id == 1
    assert result.project_id == 1
    assert result.status == TaskStatus.TODO
    assert result.created_at == EARLIER
    assert result.is_overdue is False


@pytest.mark.parametrize("due_date", [None, TODAY])
def test_create_task_with_no_or_today_due_date_succeeds(
    service: TaskService, due_date: date | None
) -> None:
    """A missing due date or today's date is allowed."""
    result = service.create_task(
        TaskCreate(project_id=1, title="Write", due_date=due_date)
    )

    assert result.due_date == due_date


def test_create_task_with_past_due_date_raises(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """A due date before today is rejected and nothing is stored."""
    data = TaskCreate(project_id=1, title="Write", due_date=date(2026, 11, 6))

    with pytest.raises(PastDueDateError):
        service.create_task(data)

    assert task_repo.tasks == {}


def test_create_task_with_missing_project_raises(service: TaskService) -> None:
    """An unknown project is rejected."""
    with pytest.raises(ProjectNotFoundError):
        service.create_task(TaskCreate(project_id=99, title="Write"))


def test_create_task_with_archived_project_raises(
    service: TaskService,
    project_repo: FakeProjectRepository,
    task_repo: FakeTaskRepository,
) -> None:
    """Archived projects accept no tasks."""
    project_repo.add_project(2, is_archived=True)

    with pytest.raises(ArchivedProjectError):
        service.create_task(TaskCreate(project_id=2, title="Write"))

    assert task_repo.tasks == {}


def test_list_tasks_without_filters_passes_none_and_returns_reads(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """Without filters the repository gets None for each one."""
    _stored_task(task_repo)

    result = service.list_tasks()

    assert task_repo.list_calls == [
        {"project_id": None, "status": None, "priority": None}
    ]
    assert [item.id for item in result] == [1]


def test_list_tasks_with_filters_passes_them_to_repository(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """Filters are forwarded untouched."""
    service.list_tasks(project_id=1, status=TaskStatus.DONE, priority=TaskPriority.LOW)

    assert task_repo.list_calls == [
        {"project_id": 1, "status": TaskStatus.DONE, "priority": TaskPriority.LOW}
    ]


def test_list_tasks_computes_is_overdue_with_clock_today(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """Overdue flags are derived from the injected clock."""
    _stored_task(task_repo, due_date=date(2026, 11, 6))
    _stored_task(task_repo, due_date=TODAY)
    _stored_task(
        task_repo,
        status=TaskStatus.DONE,
        completed_at=EARLIER,
        due_date=date(2026, 11, 6),
    )

    result = service.list_tasks()

    assert [item.is_overdue for item in result] == [True, False, False]


@pytest.mark.parametrize("status", [TaskStatus.TODO, TaskStatus.IN_PROGRESS])
def test_update_status_to_done_sets_completed_at_to_now(
    service: TaskService, task_repo: FakeTaskRepository, status: TaskStatus
) -> None:
    """Completing a task stamps completed_at with the clock."""
    task = _stored_task(task_repo, status=status)

    result = service.update_status(task.id, TaskStatus.DONE)

    assert task.status == TaskStatus.DONE
    assert task.completed_at == NOW
    assert result.completed_at == NOW
    assert result.status == TaskStatus.DONE
    assert task_repo.saved == [task]


def test_update_status_done_to_done_keeps_original_completed_at(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """Re-marking a done task does not move completed_at."""
    task = _stored_task(task_repo, TaskStatus.DONE, completed_at=EARLIER)

    result = service.update_status(task.id, TaskStatus.DONE)

    assert task.completed_at == EARLIER
    assert result.completed_at == EARLIER


@pytest.mark.parametrize("status", [TaskStatus.TODO, TaskStatus.IN_PROGRESS])
def test_update_status_leaving_done_resets_completed_at(
    service: TaskService, task_repo: FakeTaskRepository, status: TaskStatus
) -> None:
    """Reopening a task clears completed_at."""
    task = _stored_task(task_repo, TaskStatus.DONE, completed_at=EARLIER)

    result = service.update_status(task.id, status)

    assert task.status == status
    assert task.completed_at is None
    assert result.completed_at is None
    assert task_repo.saved == [task]


def test_update_status_between_open_statuses_keeps_completed_at_none(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """Moving between non-done statuses leaves completed_at null."""
    task = _stored_task(task_repo)

    service.update_status(task.id, TaskStatus.IN_PROGRESS)

    assert task.completed_at is None


def test_update_status_with_missing_task_raises(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """An unknown task is rejected and nothing is saved."""
    with pytest.raises(TaskNotFoundError):
        service.update_status(42, TaskStatus.DONE)

    assert task_repo.saved == []


def test_delete_task_with_existing_task_deletes_it(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """An existing task is removed through the repository."""
    task = _stored_task(task_repo)

    result = service.delete_task(task.id)

    assert result is None
    assert task_repo.deleted == [task]


def test_delete_task_with_missing_task_raises(
    service: TaskService, task_repo: FakeTaskRepository
) -> None:
    """An unknown task is rejected and nothing is deleted."""
    with pytest.raises(TaskNotFoundError):
        service.delete_task(42)

    assert task_repo.deleted == []
