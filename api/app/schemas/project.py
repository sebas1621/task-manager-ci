"""Pydantic schemas for projects."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

ProjectName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class ProjectCreate(BaseModel):
    """Payload to create a project.

    Attributes:
        name: Stripped, non-blank name of at most 100 characters.
        description: Optional description.
    """

    name: ProjectName
    description: str | None = None


class ProjectRead(BaseModel):
    """Project as returned by the API.

    Attributes:
        id: Primary key.
        name: Project name.
        description: Optional description.
        is_archived: Whether the project is archived.
        created_at: Creation timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_archived: bool
    created_at: datetime
