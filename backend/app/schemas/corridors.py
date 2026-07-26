from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field


class CorridorAnalysisRequest(BaseModel):
    road_id: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("roadId", "road_id"),
    )
    buffer_meters: int = Field(default=30, ge=0, le=500)


class CorridorAnalysisResponse(BaseModel):
    corridorId: str
    roadId: str
    name: str
    knownCurbRamps: int
    possibleMissingCurbCuts: int
    hydrantsNearby: int
    bikeLanesNearby: int
    userAnnotationsNearby: int
    busStopsNearby: int
    parkingConflicts: int
    bikeLaneFeasibility: Literal["Low", "Medium", "High"]
    planningNotes: list[str]
