"""Business rules for reports."""

from app.core.clock import Clock
from app.core.exceptions import ProjectNotFoundError
from app.models.enums import TaskStatus
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.report import ProjectSummary, StatusCounts
from app.schemas.task import is_overdue


class ReportService:
    """Builds read-only reports about projects."""

    def __init__(
        self,
        task_repository: TaskRepository,
        project_repository: ProjectRepository,
        clock: Clock,
    ) -> None:
        """Bind the service to its collaborators.

        Args:
            task_repository: Repository used to read tasks.
            project_repository: Repository used to validate projects.
            clock: Time source.
        """
        self._tasks = task_repository
        self._projects = project_repository
        self._clock = clock

    def project_summary(self, project_id: int) -> ProjectSummary:
        """Summarize the tasks of a project.

        Args:
            project_id: Id of the project to summarize.

        Returns:
            Totals, per-status counts, completion percentage and overdue count.

        Raises:
            ProjectNotFoundError: If the project does not exist.
        """
        if self._projects.get_by_id(project_id) is None:
            raise ProjectNotFoundError(project_id)
        tasks = self._tasks.list(project_id=project_id)
        today = self._clock.today()
        counts = StatusCounts(
            todo=sum(t.status == TaskStatus.TODO for t in tasks),
            in_progress=sum(t.status == TaskStatus.IN_PROGRESS for t in tasks),
            done=sum(t.status == TaskStatus.DONE for t in tasks),
        )
        total = len(tasks)
        percentage = round(counts.done / total * 100, 2) if total else 0.0
        return ProjectSummary(
            project_id=project_id,
            total_tasks=total,
            status_counts=counts,
            completion_percentage=percentage,
            overdue_tasks=sum(is_overdue(t, today) for t in tasks),
        )
