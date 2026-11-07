"""Unit tests for ``app.services.health_service``."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.health_service import HealthService


@pytest.fixture
def session() -> MagicMock:
    """Provide a mocked SQLAlchemy session."""
    return MagicMock(spec=Session)


def test_is_database_available_when_query_succeeds_returns_true(
    session: MagicMock,
) -> None:
    """A successful SELECT 1 means the database is available."""
    service = HealthService(session)

    result = service.is_database_available()

    assert result is True


def test_is_database_available_executes_select_one(session: MagicMock) -> None:
    """The service runs exactly one ``SELECT 1`` statement."""
    service = HealthService(session)

    service.is_database_available()

    session.execute.assert_called_once()
    statement = session.execute.call_args.args[0]
    assert str(statement) == "SELECT 1"


@pytest.mark.parametrize(
    "error",
    [
        OperationalError("SELECT 1", {}, Exception("connection refused")),
        SQLAlchemyError("boom"),
    ],
)
def test_is_database_available_when_sqlalchemy_error_returns_false(
    session: MagicMock, error: SQLAlchemyError
) -> None:
    """SQLAlchemy errors are swallowed and reported as unavailable."""
    session.execute.side_effect = error
    service = HealthService(session)

    result = service.is_database_available()

    assert result is False
