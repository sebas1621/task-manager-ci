"""FastAPI application factory."""

from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.routers import health, projects, tasks
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
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)
    return app
