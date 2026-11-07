"""Unit tests for ``app.core.exceptions``."""

from app.core.exceptions import ConflictError, DomainError, DuplicateProjectNameError


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
