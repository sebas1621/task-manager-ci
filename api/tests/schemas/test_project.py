"""Unit tests for ``app.schemas.project``."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead


def test_project_create_with_name_only_defaults_description_to_none() -> None:
    """Description is optional."""
    data = ProjectCreate(name="Alpha")

    assert data.name == "Alpha"
    assert data.description is None


def test_project_create_with_description_keeps_it() -> None:
    """A provided description is preserved."""
    data = ProjectCreate(name="Alpha", description="First project")

    assert data.description == "First project"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("  Alpha  ", "Alpha"), ("\tAlpha\n", "Alpha"), ("A b", "A b")],
)
def test_project_create_name_with_whitespace_is_stripped(
    raw: str, expected: str
) -> None:
    """Surrounding whitespace is removed from the name."""
    assert ProjectCreate(name=raw).name == expected


@pytest.mark.parametrize("name", ["", " ", "   ", "\t\n"])
def test_project_create_blank_name_raises_validation_error(name: str) -> None:
    """Empty or whitespace-only names are rejected."""
    with pytest.raises(ValidationError):
        ProjectCreate(name=name)


def test_project_create_name_of_100_chars_is_accepted() -> None:
    """The upper length bound is inclusive."""
    assert ProjectCreate(name="a" * 100).name == "a" * 100


def test_project_create_name_longer_than_100_chars_raises_validation_error() -> None:
    """Names over 100 characters are rejected."""
    with pytest.raises(ValidationError):
        ProjectCreate(name="a" * 101)


def test_project_create_length_is_measured_after_stripping() -> None:
    """Padding does not count toward the 100 character limit."""
    assert ProjectCreate(name="  " + "a" * 100 + "  ").name == "a" * 100


def test_project_create_without_name_raises_validation_error() -> None:
    """Name is required."""
    with pytest.raises(ValidationError):
        ProjectCreate.model_validate({})


def test_project_read_from_orm_instance_copies_fields() -> None:
    """ProjectRead can be built from a Project ORM object."""
    created_at = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    project = Project(
        id=7,
        name="Alpha",
        description=None,
        is_archived=False,
        created_at=created_at,
    )

    read = ProjectRead.model_validate(project)

    assert read.id == 7
    assert read.name == "Alpha"
    assert read.description is None
    assert read.is_archived is False
    assert read.created_at == created_at
