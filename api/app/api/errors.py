"""Mapping of domain errors to HTTP responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError


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


def _handle_not_found(_request: Request, exc: Exception) -> JSONResponse:
    """Translate a NotFoundError into a 404 response.

    Args:
        _request: The failing request (unused).
        exc: The raised not-found error.

    Returns:
        A 404 JSON response carrying the error message.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


def _handle_business_rule(_request: Request, exc: Exception) -> JSONResponse:
    """Translate a BusinessRuleError into a 422 response.

    Args:
        _request: The failing request (unused).
        exc: The raised business rule error.

    Returns:
        A 422 JSON response carrying the error message.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": str(exc)},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain error handlers on the application.

    Args:
        app: The FastAPI application.
    """
    app.add_exception_handler(ConflictError, _handle_conflict)
    app.add_exception_handler(NotFoundError, _handle_not_found)
    app.add_exception_handler(BusinessRuleError, _handle_business_rule)
