"""Unit tests for ``app.models.enums``."""

from enum import StrEnum

import pytest

from app.models.enums import TaskPriority, TaskStatus


@pytest.mark.parametrize("enum_cls", [TaskStatus, TaskPriority])
def test_enum_is_str_enum(enum_cls: type[StrEnum]) -> None:
    """Both enums are StrEnum subclasses."""
    assert issubclass(enum_cls, StrEnum)


def test_task_status_members_have_expected_values() -> None:
    """TaskStatus maps members to the stored string values, in order."""
    assert [(m.name, m.value) for m in TaskStatus] == [
        ("TODO", "todo"),
        ("IN_PROGRESS", "in_progress"),
        ("DONE", "done"),
    ]


def test_task_priority_members_have_expected_values() -> None:
    """TaskPriority maps members to the stored string values, in order."""
    assert [(m.name, m.value) for m in TaskPriority] == [
        ("LOW", "low"),
        ("MEDIUM", "medium"),
        ("HIGH", "high"),
    ]


@pytest.mark.parametrize(
    ("enum_cls", "raw", "member"),
    [
        (TaskStatus, "done", TaskStatus.DONE),
        (TaskPriority, "high", TaskPriority.HIGH),
    ],
)
def test_enum_from_raw_value_returns_member(
    enum_cls: type[StrEnum], raw: str, member: StrEnum
) -> None:
    """Raw strings convert to members and compare equal to strings."""
    assert enum_cls(raw) is member
    assert member == raw
