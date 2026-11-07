"""Persistence queries for tasks."""

import builtins

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task


class TaskRepository:
    """Encapsulates all SQLAlchemy access for tasks."""

    def __init__(self, session: Session) -> None:
        """Bind the repository to a session.

        Args:
            session: Database session used for every query.
        """
        self._session = session

    def add(self, task: Task) -> Task:
        """Persist a task and reload its database-generated fields.

        Args:
            task: The task to store.

        Returns:
            The same task, refreshed after the commit.
        """
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)
        return task

    def get_by_id(self, task_id: int) -> Task | None:
        """Find a task by primary key.

        Args:
            task_id: The task id.

        Returns:
            The matching task, or None.
        """
        return self._session.get(Task, task_id)

    def list(
        self,
        project_id: int | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> builtins.list[Task]:
        """List tasks ordered by id, optionally filtered.

        Args:
            project_id: Only tasks of this project, when given.
            status: Only tasks with this status, when given.
            priority: Only tasks with this priority, when given.

        Returns:
            The matching tasks.
        """
        statement = select(Task).order_by(Task.id)
        if project_id is not None:
            statement = statement.where(Task.project_id == project_id)
        if status is not None:
            statement = statement.where(Task.status == status)
        if priority is not None:
            statement = statement.where(Task.priority == priority)
        return builtins.list(self._session.scalars(statement).all())

    def save(self, task: Task) -> Task:
        """Commit pending changes of a task and reload it.

        Args:
            task: The modified task.

        Returns:
            The same task, refreshed after the commit.
        """
        self._session.commit()
        self._session.refresh(task)
        return task

    def delete(self, task: Task) -> None:
        """Delete a task and commit.

        Args:
            task: The task to remove.
        """
        self._session.delete(task)
        self._session.commit()
