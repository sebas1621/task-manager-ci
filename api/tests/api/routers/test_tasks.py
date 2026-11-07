"""Unit tests for ``app.api.routers.tasks``."""

from collections.abc import Iterator
from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_task_service
from app.core.config import Settings
from app.core.exceptions import (
    ArchivedProjectError,
    PastDueDateError,
    ProjectNotFoundError,
    TaskNotFoundError,
)
from app.main import create_app
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskRead
from app.services.task_service import TaskService

CREATED_AT = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def _settings() -> Settings:
    """Build explicit settings with fake values.

    Returns:
        A Settings instance that needs no environment.
    """
    return Settings(
        postgres_user="test-user",
        postgres_password="test-password",
        postgres_db="db",
        db_host="db-host",
    )


def _task_read(
    task_id: int = 1, status: TaskStatus = TaskStatus.TODO, is_overdue: bool = False
) -> TaskRead:
    """Build a TaskRead with every field set.

    Args:
        task_id: Identifier to assign.
        status: Task status.
        is_overdue: Overdue flag.

    Returns:
        A TaskRead instance.
    """
    return TaskRead(
        id=task_id,
        project_id=1,
        title="Write",
        description=None,
        status=status,
        priority=TaskPriority.MEDIUM,
        due_date=date(2026, 11, 20),
        created_at=CREATED_AT,
        completed_at=None,
        is_overdue=is_overdue,
    )


@pytest.fixture
def service() -> MagicMock:
    """Provide a mocked TaskService."""
    return MagicMock(spec=TaskService)


@pytest.fixture
def client(service: MagicMock) -> Iterator[TestClient]:
    """Provide a TestClient whose task service is the mock.

    Args:
        service: The mocked task service to inject.

    Yields:
        A TestClient bound to an app with the dependency overridden.
    """
    app = create_app(_settings())
    app.dependency_overrides[get_task_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_task_with_valid_body_returns_201_and_task(
    client: TestClient, service: MagicMock
) -> None:
    """A valid body yields 201 and the serialized task."""
    service.create_task.return_value = _task_read()

    response = client.post(
        "/tasks", json={"project_id": 1, "title": "Write", "due_date": "2026-11-20"}
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "project_id": 1,
        "title": "Write",
        "description": None,
        "status": "todo",
        "priority": "medium",
        "due_date": "2026-11-20",
        "created_at": "2026-11-01T12:00:00Z",
        "completed_at": None,
        "is_overdue": False,
    }


def test_create_task_passes_validated_data_to_service(
    client: TestClient, service: MagicMock
) -> None:
    """The service receives a stripped TaskCreate."""
    service.create_task.return_value = _task_read()

    client.post("/tasks", json={"project_id": 1, "title": "  Write  "})

    service.create_task.assert_called_once_with(TaskCreate(project_id=1, title="Write"))


@pytest.mark.parametrize(
    ("error", "status_code", "detail"),
    [
        (ProjectNotFoundError(9), 404, "Project 9 not found"),
        (ArchivedProjectError(2), 409, "Project 2 is archived"),
        (
            PastDueDateError(date(2026, 11, 6)),
            422,
            "Due date 2026-11-06 is in the past",
        ),
    ],
)
def test_create_task_when_service_raises_maps_error_to_http(
    client: TestClient,
    service: MagicMock,
    error: Exception,
    status_code: int,
    detail: str,
) -> None:
    """Domain errors become 404, 409 or 422 with their message."""
    service.create_task.side_effect = error

    response = client.post("/tasks", json={"project_id": 1, "title": "Write"})

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize(
    "body",
    [
        {"project_id": 1, "title": "   "},
        {"project_id": 1, "title": ""},
        {"title": "Write"},
    ],
)
def test_create_task_with_invalid_body_returns_422(
    client: TestClient, service: MagicMock, body: dict[str, object]
) -> None:
    """Blank titles and missing fields never reach the service."""
    response = client.post("/tasks", json=body)

    assert response.status_code == 422
    service.create_task.assert_not_called()


def test_list_tasks_without_params_returns_200_and_calls_service(
    client: TestClient, service: MagicMock
) -> None:
    """GET /tasks returns the serialized list with no filters."""
    service.list_tasks.return_value = [_task_read(1), _task_read(2, is_overdue=True)]

    response = client.get("/tasks")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [1, 2]
    assert response.json()[1]["is_overdue"] is True
    service.list_tasks.assert_called_once_with(
        project_id=None, status=None, priority=None
    )


def test_list_tasks_with_query_params_passes_filters_to_service(
    client: TestClient, service: MagicMock
) -> None:
    """Query parameters are parsed and forwarded as typed filters."""
    service.list_tasks.return_value = []

    response = client.get(
        "/tasks", params={"project_id": 3, "status": "done", "priority": "high"}
    )

    assert response.status_code == 200
    assert response.json() == []
    service.list_tasks.assert_called_once_with(
        project_id=3, status=TaskStatus.DONE, priority=TaskPriority.HIGH
    )


@pytest.mark.parametrize(
    "params", [{"status": "bogus"}, {"priority": "urgent"}, {"project_id": "abc"}]
)
def test_list_tasks_with_invalid_param_returns_422(
    client: TestClient, service: MagicMock, params: dict[str, str]
) -> None:
    """Invalid filter values are rejected before the service."""
    response = client.get("/tasks", params=params)

    assert response.status_code == 422
    service.list_tasks.assert_not_called()


def test_update_task_status_with_valid_body_returns_200_and_task(
    client: TestClient, service: MagicMock
) -> None:
    """A valid status yields 200 and the updated task."""
    service.update_status.return_value = _task_read(5, TaskStatus.DONE)

    response = client.patch("/tasks/5/status", json={"status": "done"})

    assert response.status_code == 200
    assert response.json()["id"] == 5
    assert response.json()["status"] == "done"
    service.update_status.assert_called_once_with(5, TaskStatus.DONE)


def test_update_task_status_with_missing_task_returns_404(
    client: TestClient, service: MagicMock
) -> None:
    """An unknown task yields 404 with the error message."""
    service.update_status.side_effect = TaskNotFoundError(5)

    response = client.patch("/tasks/5/status", json={"status": "done"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task 5 not found"}


@pytest.mark.parametrize("body", [{"status": "archived"}, {}])
def test_update_task_status_with_invalid_body_returns_422(
    client: TestClient, service: MagicMock, body: dict[str, str]
) -> None:
    """Invalid statuses never reach the service."""
    response = client.patch("/tasks/5/status", json=body)

    assert response.status_code == 422
    service.update_status.assert_not_called()


def test_delete_task_with_existing_task_returns_204_and_empty_body(
    client: TestClient, service: MagicMock
) -> None:
    """A successful delete yields 204 with no content."""
    response = client.delete("/tasks/5")

    assert response.status_code == 204
    assert response.content == b""
    service.delete_task.assert_called_once_with(5)


def test_delete_task_with_missing_task_returns_404(
    client: TestClient, service: MagicMock
) -> None:
    """An unknown task yields 404 with the error message."""
    service.delete_task.side_effect = TaskNotFoundError(5)

    response = client.delete("/tasks/5")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task 5 not found"}
