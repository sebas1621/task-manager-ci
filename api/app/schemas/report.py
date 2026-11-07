"""Pydantic schemas for reports."""

from pydantic import BaseModel


class StatusCounts(BaseModel):
    """Number of tasks per status.

    Attributes:
        todo: Tasks waiting to start.
        in_progress: Tasks being worked on.
        done: Completed tasks.
    """

    todo: int
    in_progress: int
    done: int


class ProjectSummary(BaseModel):
    """Task summary of a project.

    Attributes:
        project_id: Id of the summarized project.
        total_tasks: Total number of tasks.
        status_counts: Number of tasks per status.
        completion_percentage: Done tasks over total, 0-100, two decimals.
        overdue_tasks: Number of tasks past due and not done.
    """

    project_id: int
    total_tasks: int
    status_counts: StatusCounts
    completion_percentage: float
    overdue_tasks: int
