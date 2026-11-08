"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Runtime configuration read from environment variables.

    Attributes:
        postgres_user: Database user name.
        postgres_password: Database password (never shown in repr).
        postgres_db: Database name.
        db_host: Database host (the Compose service name).
        db_port: Database port.
        app_name: Application title shown in the API docs.
    """

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    db_host: str
    db_port: int = 5432
    app_name: str = "Task Manager API"

    @property
    def database_url(self) -> URL:
        """Build the SQLAlchemy URL for the psycopg 3 driver.

        Returns:
            A ``sqlalchemy.engine.URL`` holding the real password. Its
            ``str()`` and ``repr()`` mask the password.
        """
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings.

    Returns:
        The process-wide Settings instance.
    """
    return Settings()
