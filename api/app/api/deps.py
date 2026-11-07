"""FastAPI dependency providers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.services.health_service import HealthService

SessionDep = Annotated[Session, Depends(get_session)]


def get_health_service(session: SessionDep) -> HealthService:
    """Build a health service bound to the request session.

    Args:
        session: Database session for the current request.

    Returns:
        A HealthService instance.
    """
    return HealthService(session)
