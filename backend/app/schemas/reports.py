from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CorridorReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    road_id: str = Field(
        min_length=1,
        max_length=64,
        # Accept three name forms that appear across the codebase:
        #   corridor_id — legacy alias kept for backwards compatibility
        #   road_id     — canonical snake_case used in the API docs
        #   roadId      — camelCase used by the frontend
        validation_alias=AliasChoices("corridor_id", "road_id", "roadId"),
    )
    format: Literal["html"] = "html"


class CorridorReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reportId: str
    roadId: str
    downloadUrl: str  # Relative path — frontend prepends API_BASE_URL before opening.
    summary: str      # Human-readable status message shown in the ReportPanel.
