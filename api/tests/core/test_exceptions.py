"""Unit tests for ``app.core.exceptions``."""

from datetime import date

from app.core.exceptions import (
    ArchivedProjectError,
    BusinessRuleError,
    ConflictError,
    DomainError,
    DuplicateProjectNameError,
    NotFoundError,
    PastDueDateError,
    ProjectNotFoundError,
    TaskNotFoundError,
)


def test_domain_error_with_message_exposes_message_as_str() -> None:
    """A DomainError carries a human readable message."""
    error = DomainError("something went wrong")

    assert str(error) == "something went wrong"
    assert isinstance(error, Exception)


def test_conflict_error_is_a_domain_error() -> None:
    """ConflictError specializes DomainError."""
    assert issubclass(ConflictError, DomainError)


def test_duplicate_project_name_error_is_a_conflict_error() -> None:
    """DuplicateProjectNameError specializes ConflictError."""
    assert issubclass(DuplicateProjectNameError, ConflictError)


def test_duplicate_project_name_error_with_name_builds_message() -> None:
    """The message mentions the duplicated project name."""
    error = DuplicateProjectNameError("Alpha")

    assert str(error) == "Project with name 'Alpha' already exists"


def test_not_found_error_is_a_domain_error() -> None:
    """NotFoundError specializes DomainError."""
    assert issubclass(NotFoundError, DomainError)


def test_project_not_found_error_with_id_builds_message() -> None:
    """The message mentions the missing project id."""
    error = ProjectNotFoundError(7)

    assert isinstance(error, NotFoundError)
    assert str(error) == "Project 7 not found"


def test_task_not_found_error_with_id_builds_message() -> None:
    """The message mentions the missing task id."""
    error = TaskNotFoundError(3)

    assert isinstance(error, NotFoundError)
    assert str(error) == "Task 3 not found"


def test_archived_project_error_with_id_builds_message() -> None:
    """The message mentions the archived project id."""
    error = ArchivedProjectError(5)

    assert isinstance(error, ConflictError)
    assert str(error) == "Project 5 is archived"


def test_business_rule_error_is_a_domain_error() -> None:
    """BusinessRuleError specializes DomainError."""
    assert issubclass(BusinessRuleError, DomainError)


def test_past_due_date_error_with_date_builds_message() -> None:
    """The message contains the ISO formatted due date."""
    error = PastDueDateError(date(2026, 11, 6))

    assert isinstance(error, BusinessRuleError)
    assert str(error) == "Due date 2026-11-06 is in the past"
