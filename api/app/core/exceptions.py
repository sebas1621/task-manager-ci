"""Domain exceptions raised by the service layer."""


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
