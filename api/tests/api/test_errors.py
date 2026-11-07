"""Unit tests for ``app.api.errors``."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.errors import register_exception_handlers
from app.core.exceptions import ConflictError, DuplicateProjectNameError


@pytest.fixture
def client() -> TestClient:
    """Provide a tiny app with handlers and routes raising domain errors.

    Returns:
        A TestClient for the app.
    """
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/duplicate")
    def duplicate() -> None:
        raise DuplicateProjectNameError("Alpha")

    @app.get("/conflict")
    def conflict() -> None:
        raise ConflictError("generic conflict")

    return TestClient(app)


def test_duplicate_project_error_returns_409_with_detail(client: TestClient) -> None:
    """A duplicate project error maps to 409 and its message."""
    response = client.get("/duplicate")

    assert response.status_code == 409
    assert response.json() == {"detail": "Project with name 'Alpha' already exists"}


def test_conflict_error_returns_409_with_detail(client: TestClient) -> None:
    """Any ConflictError maps to 409."""
    response = client.get("/conflict")

    assert response.status_code == 409
    assert response.json() == {"detail": "generic conflict"}
