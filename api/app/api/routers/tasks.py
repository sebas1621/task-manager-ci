"""Tasks router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi import status as http_status

from app.api.deps import get_task_service
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskStatusUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


@router.post(
    "",
    response_model=TaskRead,
    status_code=http_status.HTTP_201_CREATED,
    responses={
        http_status.HTTP_404_NOT_FOUND: {"description": "Project not found"},
        http_status.HTTP_409_CONFLICT: {"description": "Project is archived"},
        http_status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Invalid payload or due date in the past"
        },
    },
)
def create_task(data: TaskCreate, service: TaskServiceDep) -> TaskRead:
    """Create a task.

    Args:
        data: Validated creation payload.
        service: Task service.

    Returns:
        The created task.
    """
    return service.create_task(data)


@router.get("", response_model=list[TaskRead])
def list_tasks(
    service: TaskServiceDep,
    project_id: int | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
) -> list[TaskRead]:
    """List tasks, optionally filtered.

    Args:
        service: Task service.
        project_id: Only tasks of this project.
        status: Only tasks with this status.
        priority: Only tasks with this priority.

    Returns:
        The matching tasks ordered by id.
    """
    return service.list_tasks(project_id=project_id, status=status, priority=priority)


@router.patch(
    "/{task_id}/status",
    response_model=TaskRead,
    responses={
        http_status.HTTP_404_NOT_FOUND: {"description": "Task not found"},
        http_status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Invalid status"},
    },
)
def update_task_status(
    task_id: int, data: TaskStatusUpdate, service: TaskServiceDep
) -> TaskRead:
    """Change the status of a task.

    Args:
        task_id: Id of the task.
        data: Payload with the new status.
        service: Task service.

    Returns:
        The updated task.
    """
    return service.update_status(task_id, data.status)


@router.delete(
    "/{task_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    responses={http_status.HTTP_404_NOT_FOUND: {"description": "Task not found"}},
)
def delete_task(task_id: int, service: TaskServiceDep) -> Response:
    """Delete a task.

    Args:
        task_id: Id of the task.
        service: Task service.

    Returns:
        An empty 204 response.
    """
    service.delete_task(task_id)
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)
