"""Time source abstraction so business rules stay deterministic in tests."""

from datetime import UTC, date, datetime
from typing import Protocol


class Clock(Protocol):
    """Provides the current instant and date."""

    def now(self) -> datetime:
        """Return the current timezone-aware instant."""
        ...

    def today(self) -> date:
        """Return the current date."""
        ...


class SystemClock:
    """Clock backed by the system time in UTC."""

    def now(self) -> datetime:
        """Return the current instant.

        Returns:
            A timezone-aware UTC datetime.
        """
        return datetime.now(UTC)

    def today(self) -> date:
        """Return the current UTC date.

        Returns:
            The UTC calendar date of now.
        """
        return self.now().date()
