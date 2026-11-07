"""Reports router."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import status as http_status

from app.api.deps import get_report_service
from app.schemas.report import ProjectSummary
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])

ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


@router.get(
    "/projects/{project_id}/summary",
    response_model=ProjectSummary,
    responses={http_status.HTTP_404_NOT_FOUND: {"description": "Project not found"}},
)
def get_project_summary(project_id: int, service: ReportServiceDep) -> ProjectSummary:
    """Summarize the tasks of a project.

    Args:
        project_id: Id of the project.
        service: Report service.

    Returns:
        The project summary.
    """
    return service.project_summary(project_id)
