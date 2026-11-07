"""Unit tests for ``app.api.deps``."""

from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.api.deps import get_health_service
from app.services.health_service import HealthService


def test_get_health_service_with_session_returns_bound_service() -> None:
    """The provider builds a HealthService around the given session."""
    session = MagicMock(spec=Session)

    service = get_health_service(session)

    assert isinstance(service, HealthService)
    service.is_database_available()
    session.execute.assert_called_once()
