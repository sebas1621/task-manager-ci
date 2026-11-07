"""Mapping of domain errors to HTTP responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import ConflictError


def _handle_conflict(_request: Request, exc: Exception) -> JSONResponse:
    """Translate a ConflictError into a 409 response.

    Args:
        _request: The failing request (unused).
        exc: The raised conflict error.

    Returns:
        A 409 JSON response carrying the error message.
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain error handlers on the application.

    Args:
        app: The FastAPI application.
    """
    app.add_exception_handler(ConflictError, _handle_conflict)
