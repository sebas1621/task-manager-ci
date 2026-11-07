"""FastAPI application factory."""

from fastapi import FastAPI

from app.api.routers import health
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application.

    Args:
        settings: Optional settings; loaded from the environment when omitted.

    Returns:
        The configured FastAPI application.
    """
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    return app
