"""Unit tests for ``app.models.task`` (metadata inspection only)."""

import pytest
from sqlalchemy import CheckConstraint, Date, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.db.base import Base
from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task


def _ddl() -> str:
    """Compile the CREATE TABLE statement for ``tasks`` on PostgreSQL.

    Returns:
        The DDL text.
    """
    return str(CreateTable(Task.__table__).compile(dialect=postgresql.dialect()))


def test_task_is_declarative_model_for_tasks_table() -> None:
    """Task extends Base and maps to the ``tasks`` table."""
    assert issubclass(Task, Base)
    assert Task.__tablename__ == "tasks"


def test_task_has_exactly_expected_columns() -> None:
    """No columns beyond the domain model exist."""
    assert Task.__table__.c.keys() == [
        "id",
        "project_id",
        "title",
        "description",
        "status",
        "priority",
        "due_date",
        "created_at",
        "completed_at",
    ]


@pytest.mark.parametrize(
    ("column", "type_cls", "nullable"),
    [
        ("id", Integer, False),
        ("project_id", Integer, False),
        ("title", String, False),
        ("description", Text, True),
        ("status", Enum, False),
        ("priority", Enum, False),
        ("due_date", Date, True),
        ("created_at", DateTime, False),
        ("completed_at", DateTime, True),
    ],
)
def test_task_column_has_expected_type_and_nullability(
    column: str, type_cls: type, nullable: bool
) -> None:
    """Each column has the agreed type and nullability."""
    col = Task.__table__.c[column]
    assert isinstance(col.type, type_cls)
    assert col.nullable is nullable


def test_task_id_is_primary_key() -> None:
    """``id`` is the only primary key column."""
    assert [c.name for c in Task.__table__.primary_key.columns] == ["id"]


def test_task_title_is_string_200() -> None:
    """``title`` is limited to 200 characters."""
    assert Task.__table__.c.title.type.length == 200


@pytest.mark.parametrize("column", ["created_at", "completed_at"])
def test_task_timestamp_columns_are_timezone_aware(column: str) -> None:
    """Timestamps store timezone-aware values."""
    assert Task.__table__.c[column].type.timezone is True


def test_task_project_id_foreign_key_restricts_delete() -> None:
    """``project_id`` references ``projects.id`` with ON DELETE RESTRICT."""
    foreign_keys = list(Task.__table__.c.project_id.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == "projects.id"
    assert foreign_keys[0].ondelete == "RESTRICT"
    assert "CONSTRAINT fk_tasks_project_id_projects FOREIGN KEY" in _ddl()


@pytest.mark.parametrize(
    ("column", "enum_cls", "type_name", "values"),
    [
        ("status", TaskStatus, "task_status", ["todo", "in_progress", "done"]),
        ("priority", TaskPriority, "task_priority", ["low", "medium", "high"]),
    ],
)
def test_task_enum_column_is_native_enum_stored_by_value(
    column: str, enum_cls: type, type_name: str, values: list[str]
) -> None:
    """Enum columns use a named PostgreSQL enum holding the values."""
    col_type = Task.__table__.c[column].type
    assert col_type.enum_class is enum_cls
    assert col_type.name == type_name
    assert col_type.native_enum is True
    assert list(col_type.enums) == values


def test_task_enum_server_defaults_in_ddl() -> None:
    """Status and priority defaults are set by the database."""
    ddl = _ddl()
    assert "status task_status DEFAULT 'todo' NOT NULL" in ddl
    assert "priority task_priority DEFAULT 'medium' NOT NULL" in ddl


def test_task_created_at_server_default_is_now() -> None:
    """``created_at`` defaults to ``now()`` in the database."""
    assert "created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL" in _ddl()


def test_task_check_constraints_have_expected_names() -> None:
    """Both business-rule checks exist under their convention names."""
    names = {
        str(c.name)
        for c in Task.__table__.constraints
        if isinstance(c, CheckConstraint)
    }
    assert names == {
        "ck_tasks_title_not_blank",
        "ck_tasks_completed_at_matches_status",
    }


def test_task_title_check_rejects_blank_titles_in_ddl() -> None:
    """The title check trims whitespace and requires a non-empty result."""
    ddl = _ddl()
    assert "CONSTRAINT ck_tasks_title_not_blank CHECK" in ddl
    assert "trim(title)" in ddl.lower()


def test_task_completed_at_check_matches_status_in_ddl() -> None:
    """``completed_at`` is set exactly when status is ``done``."""
    ddl = _ddl()
    assert "CONSTRAINT ck_tasks_completed_at_matches_status CHECK" in ddl
    assert "completed_at IS NOT NULL" in ddl
    assert "'done'" in ddl


def test_task_has_only_project_status_composite_index() -> None:
    """The only index is (project_id, status)."""
    indexes = {str(i.name): [c.name for c in i.columns] for i in Task.__table__.indexes}
    assert indexes == {"ix_tasks_project_id_status": ["project_id", "status"]}
