"""Unit tests for the ``app.models`` package exports.

Named ``test_package`` because ``test___init__`` would be unreadable.
"""

import app.models as models
from app.db.base import Base
from app.models.enums import TaskPriority, TaskStatus
from app.models.project import Project
from app.models.task import Task


def test_package_exposes_models_and_enums() -> None:
    """The package re-exports the public models and enums."""
    assert models.Project is Project
    assert models.Task is Task
    assert models.TaskStatus is TaskStatus
    assert models.TaskPriority is TaskPriority


def test_package_registers_both_tables_in_metadata() -> None:
    """Importing the package registers every table in Base.metadata."""
    assert {"projects", "tasks"} <= set(Base.metadata.tables)
