from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field


class CorridorReportRequest(BaseModel):
    road_id: str = Field(
        min_length=1,
        max_length=64,
        # Accept three name forms that appear across the codebase:
        #   corridor_id — legacy alias kept for backwards compatibility
        #   road_id     — canonical snake_case used in the API docs
        #   roadId      — camelCase used by the frontend
        validation_alias=AliasChoices("corridor_id", "road_id", "roadId"),
    )
    format: str = "html"  # Only "html" is implemented; reserved for future PDF/CSV.


class CorridorReportResponse(BaseModel):
    reportId: str
    roadId: str
    downloadUrl: str  # Relative path — frontend prepends API_BASE_URL before opening.
    summary: str      # Human-readable status message shown in the ReportPanel.
