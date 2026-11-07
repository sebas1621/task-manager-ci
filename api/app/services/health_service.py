"""Health check business logic."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class HealthService:
    """Checks the availability of the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the service.

        Args:
            session: Database session used for the probe query.
        """
        self._session = session

    def is_database_available(self) -> bool:
        """Run ``SELECT 1`` against the database.

        Returns:
            True if the query succeeds, False on any SQLAlchemy error.
        """
        try:
            self._session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True
