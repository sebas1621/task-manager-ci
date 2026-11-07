"""Unit tests for ``app.db.base``."""

import pytest
from sqlalchemy.orm import DeclarativeBase

from app.db.base import NAMING_CONVENTION, Base


def test_base_is_declarative_base_subclass() -> None:
    """Base must be a SQLAlchemy 2.0 declarative base."""
    assert issubclass(Base, DeclarativeBase)


@pytest.mark.parametrize(
    ("key", "template"),
    [
        ("ix", "ix_%(column_0_label)s"),
        ("uq", "uq_%(table_name)s_%(column_0_name)s"),
        ("ck", "ck_%(table_name)s_%(constraint_name)s"),
        (
            "fk",
            "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        ),
        ("pk", "pk_%(table_name)s"),
    ],
)
def test_naming_convention_key_has_expected_template(key: str, template: str) -> None:
    """Each constraint kind uses its agreed naming template."""
    assert NAMING_CONVENTION[key] == template


def test_naming_convention_has_only_expected_keys() -> None:
    """No unexpected naming rules are defined."""
    assert set(NAMING_CONVENTION) == {"ix", "uq", "ck", "fk", "pk"}


def test_base_metadata_uses_naming_convention() -> None:
    """Base.metadata must apply NAMING_CONVENTION."""
    assert Base.metadata.naming_convention == NAMING_CONVENTION
