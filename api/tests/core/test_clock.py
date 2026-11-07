"""Unit tests for ``app.core.clock``."""

from datetime import UTC, date, datetime, timedelta, tzinfo
from unittest.mock import patch

from app.core.clock import SystemClock

FIXED = datetime(2026, 11, 7, 23, 30, tzinfo=UTC)


class FrozenDatetime(datetime):
    """Datetime subclass whose ``now`` always returns a fixed instant."""

    @classmethod
    def now(cls, tz: tzinfo | None = None) -> "FrozenDatetime":
        """Return the frozen instant converted to ``tz``.

        Args:
            tz: Optional timezone.

        Returns:
            The fixed instant.
        """
        return cls.fromtimestamp(FIXED.timestamp(), tz)


def test_system_clock_now_returns_timezone_aware_utc_datetime() -> None:
    """now() is a UTC-aware datetime."""
    result = SystemClock().now()

    assert isinstance(result, datetime)
    assert result.utcoffset() == timedelta(0)


def test_system_clock_now_returns_patched_instant() -> None:
    """now() reads the module's datetime source."""
    with patch("app.core.clock.datetime", FrozenDatetime):
        result = SystemClock().now()

    assert result == FIXED


def test_system_clock_today_returns_current_utc_date() -> None:
    """today() is the UTC date of the current instant."""
    with patch("app.core.clock.datetime", FrozenDatetime):
        result = SystemClock().today()

    assert result == date(2026, 11, 7)
    assert type(result) is date
