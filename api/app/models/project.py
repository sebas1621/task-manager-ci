"""ORM model for projects."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    """A project that groups tasks.

    Attributes:
        id: Primary key.
        name: Unique project name.
        description: Optional description.
        is_archived: Whether the project is archived.
        created_at: Creation timestamp set by the database.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(Boolean, server_default=false())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
