from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field


class CorridorReportRequest(BaseModel):
    road_id: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("corridor_id", "road_id", "roadId"),
    )
    format: str = "html"


class CorridorReportResponse(BaseModel):
    reportId: str
    roadId: str
    downloadUrl: str
    summary: str
