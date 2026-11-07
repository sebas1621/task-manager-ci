"""Unit tests for ``app.schemas.report``."""

from app.schemas.report import ProjectSummary, StatusCounts


def test_status_counts_with_values_exposes_each_count() -> None:
    """Each status count is stored as given."""
    counts = StatusCounts(todo=1, in_progress=2, done=3)

    assert (counts.todo, counts.in_progress, counts.done) == (1, 2, 3)


def test_project_summary_serializes_to_expected_json_shape() -> None:
    """The summary dumps to the documented JSON structure."""
    summary = ProjectSummary(
        project_id=7,
        total_tasks=3,
        status_counts=StatusCounts(todo=1, in_progress=1, done=1),
        completion_percentage=33.33,
        overdue_tasks=2,
    )

    assert summary.model_dump(mode="json") == {
        "project_id": 7,
        "total_tasks": 3,
        "status_counts": {"todo": 1, "in_progress": 1, "done": 1},
        "completion_percentage": 33.33,
        "overdue_tasks": 2,
    }
