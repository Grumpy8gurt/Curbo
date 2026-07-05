from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, value: list[float]) -> list[float]:
        if len(value) != 2:
            raise ValueError("Point coordinates must contain longitude and latitude")
        return value


class DetectionItem(BaseModel):
    label: Literal[
        "possible_curb_cut",
        "possible_missing_curb_cut",
        "driveway",
        "sidewalk_obstruction",
        "unknown",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[int]
    estimated_location: PointGeometry | None = None
    review_status: Literal["pending"] = "pending"

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: list[int]) -> list[int]:
        if len(value) != 4:
            raise ValueError("bbox must contain four integers")
        return value


class DetectionResponse(BaseModel):
    image_id: str | None = None
    model_version: str
    detections: list[DetectionItem]
