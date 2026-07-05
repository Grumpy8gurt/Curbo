from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CorridorAnalysisRequest(BaseModel):
    road_id: str = Field(min_length=1, max_length=64)
    buffer_meters: int = Field(default=30, ge=0, le=500)


class CorridorAnalysisResponse(BaseModel):
    road_id: str
    road_name: str
    length_meters: int
    known_curb_ramps: int
    possible_missing_curb_cuts: int
    hydrants: int
    bus_stops: int
    parking_conflicts: int
    bike_lane_feasibility: Literal["low", "medium", "high"]
    notes: list[str]
