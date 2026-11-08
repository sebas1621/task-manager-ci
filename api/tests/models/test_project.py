"""Unit tests for ``app.models.project`` (metadata inspection only)."""

import pytest
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.db.base import Base
from app.models.project import Project


def _ddl() -> str:
    """Compile the CREATE TABLE statement for ``projects`` on PostgreSQL.

    Returns:
        The DDL text.
    """
    return str(CreateTable(Project.__table__).compile(dialect=postgresql.dialect()))


def test_project_is_declarative_model_for_projects_table() -> None:
    """Project extends Base and maps to the ``projects`` table."""
    assert issubclass(Project, Base)
    assert Project.__tablename__ == "projects"


def test_project_has_exactly_expected_columns() -> None:
    """No columns beyond the domain model exist."""
    columns = Project.__table__.c.keys()
    assert columns == ["id", "name", "description", "is_archived", "created_at"]


@pytest.mark.parametrize(
    ("column", "type_cls", "nullable"),
    [
        ("id", Integer, False),
        ("name", String, False),
        ("description", Text, True),
        ("is_archived", Boolean, False),
        ("created_at", DateTime, False),
    ],
)
def test_project_column_has_expected_type_and_nullability(
    column: str, type_cls: type, nullable: bool
) -> None:
    """Each column has the agreed type and nullability."""
    col = Project.__table__.c[column]
    assert isinstance(col.type, type_cls)
    assert col.nullable is nullable


def test_project_id_is_primary_key() -> None:
    """``id`` is the only primary key column."""
    assert [c.name for c in Project.__table__.primary_key.columns] == ["id"]


def test_project_name_is_string_100() -> None:
    """``name`` is limited to 100 characters."""
    assert Project.__table__.c.name.type.length == 100


def test_project_name_has_named_unique_constraint() -> None:
    """``name`` is unique through the ``uq_projects_name`` constraint."""
    assert "CONSTRAINT uq_projects_name UNIQUE (name)" in _ddl()
    uniques = [
        c for c in Project.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    assert [[col.name for col in c.columns] for c in uniques] == [["name"]]


def test_project_created_at_is_timezone_aware() -> None:
    """``created_at`` stores timezone-aware timestamps."""
    assert Project.__table__.c.created_at.type.timezone is True


def test_project_server_defaults_in_ddl() -> None:
    """Defaults are enforced by the database, not by Python."""
    ddl = _ddl()
    assert "is_archived BOOLEAN DEFAULT false NOT NULL" in ddl
    assert "created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL" in ddl


def test_project_primary_key_constraint_is_named() -> None:
    """The primary key follows the naming convention."""
    assert "CONSTRAINT pk_projects PRIMARY KEY (id)" in _ddl()
