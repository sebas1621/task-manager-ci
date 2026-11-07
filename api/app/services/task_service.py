"""Business rules for tasks."""

from app.core.clock import Clock
from app.core.exceptions import (
    ArchivedProjectError,
    PastDueDateError,
    ProjectNotFoundError,
    TaskNotFoundError,
)
from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskRead


class TaskService:
    """Creates, lists, updates and deletes tasks."""

    def __init__(
        self,
        task_repository: TaskRepository,
        project_repository: ProjectRepository,
        clock: Clock,
    ) -> None:
        """Bind the service to its collaborators.

        Args:
            task_repository: Repository used for task persistence.
            project_repository: Repository used to validate projects.
            clock: Time source.
        """
        self._tasks = task_repository
        self._projects = project_repository
        self._clock = clock

    def create_task(self, data: TaskCreate) -> TaskRead:
        """Create a task in an existing, active project.

        Args:
            data: Validated creation payload.

        Returns:
            The persisted task.

        Raises:
            ProjectNotFoundError: If the project does not exist.
            ArchivedProjectError: If the project is archived.
            PastDueDateError: If the due date is before today.
        """
        project = self._projects.get_by_id(data.project_id)
        if project is None:
            raise ProjectNotFoundError(data.project_id)
        if project.is_archived:
            raise ArchivedProjectError(data.project_id)
        today = self._clock.today()
        if data.due_date is not None and data.due_date < today:
            raise PastDueDateError(data.due_date)
        task = self._tasks.add(
            Task(
                project_id=data.project_id,
                title=data.title,
                description=data.description,
                status=TaskStatus.TODO,
                priority=data.priority,
                due_date=data.due_date,
            )
        )
        return TaskRead.from_task(task, today)

    def list_tasks(
        self,
        project_id: int | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> list[TaskRead]:
        """List tasks, optionally filtered.

        Args:
            project_id: Only tasks of this project, when given.
            status: Only tasks with this status, when given.
            priority: Only tasks with this priority, when given.

        Returns:
            The matching tasks.
        """
        today = self._clock.today()
        tasks = self._tasks.list(
            project_id=project_id, status=status, priority=priority
        )
        return [TaskRead.from_task(task, today) for task in tasks]

    def update_status(self, task_id: int, status: TaskStatus) -> TaskRead:
        """Change a task status, maintaining ``completed_at``.

        Args:
            task_id: Id of the task to update.
            status: The new status.

        Returns:
            The updated task.

        Raises:
            TaskNotFoundError: If the task does not exist.
        """
        task = self._get_or_raise(task_id)
        if status != TaskStatus.DONE:
            task.completed_at = None
        elif task.status != TaskStatus.DONE:
            task.completed_at = self._clock.now()
        task.status = status
        return TaskRead.from_task(self._tasks.save(task), self._clock.today())

    def delete_task(self, task_id: int) -> None:
        """Delete a task.

        Args:
            task_id: Id of the task to delete.

        Raises:
            TaskNotFoundError: If the task does not exist.
        """
        self._tasks.delete(self._get_or_raise(task_id))

    def _get_or_raise(self, task_id: int) -> Task:
        """Fetch a task or fail.

        Args:
            task_id: The task id.

        Returns:
            The stored task.

        Raises:
            TaskNotFoundError: If the task does not exist.
        """
        task = self._tasks.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
