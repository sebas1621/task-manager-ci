"""ORM model for tasks."""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TaskPriority, TaskStatus


def _enum_values(enum_cls: type[TaskStatus] | type[TaskPriority]) -> list[str]:
    """Return the stored values of an enum.

    Args:
        enum_cls: The enum class.

    Returns:
        The member values, in definition order.
    """
    return [member.value for member in enum_cls]


class Task(Base):
    """A unit of work that belongs to a project.

    Attributes:
        id: Primary key.
        project_id: Owning project.
        title: Non-blank title.
        description: Optional description.
        status: Lifecycle status.
        priority: Priority level.
        due_date: Optional due date.
        created_at: Creation timestamp set by the database.
        completed_at: Set exactly when the status is ``done``.
    """

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="title_not_blank"),
        CheckConstraint(
            "(status = 'done' AND completed_at IS NOT NULL)"
            " OR (status <> 'done' AND completed_at IS NULL)",
            name="completed_at_matches_status",
        ),
        Index("ix_tasks_project_id_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", values_callable=_enum_values),
        server_default=TaskStatus.TODO.value,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority", values_callable=_enum_values),
        server_default=TaskPriority.MEDIUM.value,
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
