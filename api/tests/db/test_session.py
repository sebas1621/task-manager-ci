"""Unit tests for ``app.db.session`` (engine and session mocked)."""

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import get_settings
from app.db.session import get_engine, get_session, get_session_factory


@pytest.fixture(autouse=True)
def clear_db_caches() -> Iterator[None]:
    """Clear the engine and session factory caches around each test.

    Yields:
        None, once the caches are empty.
    """
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    yield
    get_engine.cache_clear()
    get_session_factory.cache_clear()


@pytest.mark.usefixtures("full_env")
def test_get_engine_creates_engine_with_settings_url_and_pre_ping() -> None:
    """The engine uses the settings URL, pool_pre_ping and a connect timeout."""
    with patch("app.db.session.create_engine") as create_engine:
        engine = get_engine()

    create_engine.assert_called_once_with(
        get_settings().database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )
    assert engine is create_engine.return_value


@pytest.mark.usefixtures("full_env")
def test_get_engine_called_twice_returns_cached_engine() -> None:
    """The engine is created only once per process."""
    with patch("app.db.session.create_engine") as create_engine:
        first = get_engine()
        second = get_engine()

    assert first is second
    create_engine.assert_called_once()


def test_get_session_factory_builds_sessionmaker_with_expected_options() -> None:
    """The factory is bound to the engine with autoflush off."""
    with (
        patch("app.db.session.get_engine") as engine_getter,
        patch("app.db.session.sessionmaker") as sessionmaker_cls,
    ):
        factory = get_session_factory()

    sessionmaker_cls.assert_called_once_with(
        bind=engine_getter.return_value,
        autoflush=False,
        expire_on_commit=False,
    )
    assert factory is sessionmaker_cls.return_value


def test_get_session_factory_called_twice_returns_cached_factory() -> None:
    """The session factory is created only once per process."""
    with (
        patch("app.db.session.get_engine"),
        patch("app.db.session.sessionmaker") as sessionmaker_cls,
    ):
        first = get_session_factory()
        second = get_session_factory()

    assert first is second
    sessionmaker_cls.assert_called_once()


def test_get_session_yields_session_from_factory() -> None:
    """The dependency yields the session created by the factory."""
    factory = MagicMock()
    with patch("app.db.session.get_session_factory", return_value=factory):
        generator = get_session()
        session = next(generator)

        assert session is factory.return_value
        session.close.assert_not_called()
        generator.close()


def test_get_session_when_consumer_finishes_closes_session() -> None:
    """The session is closed after normal exhaustion of the generator."""
    factory = MagicMock()
    with patch("app.db.session.get_session_factory", return_value=factory):
        generator = get_session()
        session = next(generator)
        with pytest.raises(StopIteration):
            next(generator)

    session.close.assert_called_once_with()


def test_get_session_when_consumer_raises_closes_session() -> None:
    """The session is closed even when the consumer raises."""
    factory = MagicMock()
    with patch("app.db.session.get_session_factory", return_value=factory):
        generator = get_session()
        session = next(generator)
        with pytest.raises(RuntimeError, match="boom"):
            generator.throw(RuntimeError("boom"))

    session.close.assert_called_once_with()
