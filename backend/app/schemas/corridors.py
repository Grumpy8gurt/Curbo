from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field


class CorridorAnalysisRequest(BaseModel):
    road_id: str = Field(
        min_length=1,
        max_length=64,
        # Accept camelCase from the frontend (roadId) and snake_case from
        # API docs / curl examples (road_id) without a separate transformer.
        validation_alias=AliasChoices("roadId", "road_id"),
    )
    # Buffer distance in metres around the road geometry used to count nearby
    # features.  Defaults to 30 m (roughly one lane width on each side).
    buffer_meters: int = Field(default=30, ge=0, le=500)


class CorridorAnalysisResponse(BaseModel):
    """
    Corridor planning summary returned by POST /api/corridors/analyze.

    Fields use camelCase to match the frontend TypeScript type (CorridorSummary)
    without requiring an alias on the response side.
    """
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
