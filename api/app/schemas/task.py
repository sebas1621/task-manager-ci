"""Pydantic schemas for tasks."""

from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, StringConstraints

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task

TaskTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class TaskCreate(BaseModel):
    """Payload to create a task.

    Attributes:
        project_id: Owning project id.
        title: Stripped, non-blank title of at most 200 characters.
        description: Optional description.
        priority: Priority level, medium by default.
        due_date: Optional due date.
    """

    project_id: int
    title: TaskTitle
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None


class TaskStatusUpdate(BaseModel):
    """Payload to change a task status.

    Attributes:
        status: The new status.
    """

    status: TaskStatus


class TaskRead(BaseModel):
    """Task as returned by the API.

    Attributes:
        id: Primary key.
        project_id: Owning project id.
        title: Task title.
        description: Optional description.
        status: Lifecycle status.
        priority: Priority level.
        due_date: Optional due date.
        created_at: Creation timestamp.
        completed_at: Completion timestamp, set only when done.
        is_overdue: True when past due and not done.
    """

    id: int
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    created_at: datetime
    completed_at: datetime | None
    is_overdue: bool

    @classmethod
    def from_task(cls, task: Task, today: date) -> Self:
        """Build the read model from an ORM task.

        Args:
            task: The persisted task.
            today: Reference date used to compute ``is_overdue``.

        Returns:
            The serializable task.
        """
        return cls(
            id=task.id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            created_at=task.created_at,
            completed_at=task.completed_at,
            is_overdue=(
                task.due_date is not None
                and task.due_date < today
                and task.status != TaskStatus.DONE
            ),
        )
