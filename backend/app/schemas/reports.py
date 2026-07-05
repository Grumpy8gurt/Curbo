from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CorridorReportRequest(BaseModel):
    road_id: str = Field(min_length=1, max_length=64)
    include_layers: list[str] = Field(default_factory=list)


class CorridorReportResponse(BaseModel):
    report_id: str
    download_url: str
    summary: dict[str, Any]
