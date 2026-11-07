"""Domain exceptions raised by the service layer."""

from datetime import date


class DomainError(Exception):
    """Base class for all business rule violations."""


class ConflictError(DomainError):
    """Raised when an operation conflicts with existing state."""


class DuplicateProjectNameError(ConflictError):
    """Raised when a project name is already taken."""

    def __init__(self, name: str) -> None:
        """Build the error message from the duplicated name.

        Args:
            name: The project name that already exists.
        """
        super().__init__(f"Project with name '{name}' already exists")


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""


class ProjectNotFoundError(NotFoundError):
    """Raised when a project id does not exist."""

    def __init__(self, project_id: int) -> None:
        """Build the error message from the missing id.

        Args:
            project_id: The project id that was not found.
        """
        super().__init__(f"Project {project_id} not found")


class TaskNotFoundError(NotFoundError):
    """Raised when a task id does not exist."""

    def __init__(self, task_id: int) -> None:
        """Build the error message from the missing id.

        Args:
            task_id: The task id that was not found.
        """
        super().__init__(f"Task {task_id} not found")


class ArchivedProjectError(ConflictError):
    """Raised when a task is created in an archived project."""

    def __init__(self, project_id: int) -> None:
        """Build the error message from the archived project id.

        Args:
            project_id: The archived project id.
        """
        super().__init__(f"Project {project_id} is archived")


class BusinessRuleError(DomainError):
    """Raised when a payload is well formed but violates a business rule."""


class PastDueDateError(BusinessRuleError):
    """Raised when a task is created with a due date in the past."""

    def __init__(self, due_date: date) -> None:
        """Build the error message from the rejected date.

        Args:
            due_date: The due date that is in the past.
        """
        super().__init__(f"Due date {due_date.isoformat()} is in the past")
