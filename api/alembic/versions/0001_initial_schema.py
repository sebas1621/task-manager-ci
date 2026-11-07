"""Create projects and tasks tables.

Revision ID: 0001
Revises:
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the enum types, tables, constraints and index."""
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_archived", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
        sa.UniqueConstraint("name", name=op.f("uq_projects_name")),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "todo", "in_progress", "done", name="task_status", create_type=True
            ),
            server_default="todo",
            nullable=False,
        ),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "low", "medium", "high", name="task_priority", create_type=True
            ),
            server_default="medium",
            nullable=False,
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(trim(title)) > 0", name=op.f("ck_tasks_title_not_blank")
        ),
        sa.CheckConstraint(
            "(status = 'done' AND completed_at IS NOT NULL)"
            " OR (status <> 'done' AND completed_at IS NULL)",
            name=op.f("ck_tasks_completed_at_matches_status"),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_tasks_project_id_projects"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(
        "ix_tasks_project_id_status", "tasks", ["project_id", "status"], unique=False
    )


def downgrade() -> None:
    """Drop the index, tables and enum types."""
    op.drop_index("ix_tasks_project_id_status", table_name="tasks")
    op.drop_table("tasks")
    op.drop_table("projects")
    postgresql.ENUM(name="task_priority").drop(op.get_bind(), checkfirst=False)
    postgresql.ENUM(name="task_status").drop(op.get_bind(), checkfirst=False)
