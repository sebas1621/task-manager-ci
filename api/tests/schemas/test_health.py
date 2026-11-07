"""Unit tests for ``app.schemas.health``."""

import pytest
from pydantic import ValidationError

from app.schemas.health import HealthResponse


def test_health_response_with_valid_fields_exposes_values() -> None:
    """Valid fields are stored on the model."""
    response = HealthResponse(status="ok", database="ok")

    assert response.status == "ok"
    assert response.database == "ok"


def test_health_response_model_dump_returns_expected_dict() -> None:
    """Serialization yields exactly the two documented keys."""
    response = HealthResponse(status="error", database="unavailable")

    assert response.model_dump() == {"status": "error", "database": "unavailable"}


@pytest.mark.parametrize("missing", ["status", "database"])
def test_health_response_missing_field_raises_validation_error(missing: str) -> None:
    """Both fields are required."""
    data = {"status": "ok", "database": "ok"}
    del data[missing]

    with pytest.raises(ValidationError):
        HealthResponse(**data)
