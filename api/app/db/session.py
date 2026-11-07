"""Engine and session management."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create the process-wide engine from the application settings.

    Returns:
        The cached SQLAlchemy engine.
    """
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create the process-wide session factory.

    Returns:
        The cached session factory bound to the engine.
    """
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Yield a database session and always close it afterwards.

    Yields:
        A new SQLAlchemy session.
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
