"""Schemas for the health endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check payload.

    Attributes:
        status: Overall service status.
        database: Database connectivity status.
    """

    status: str
    database: str
