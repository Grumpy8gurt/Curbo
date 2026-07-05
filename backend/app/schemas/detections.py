from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.geojson import PointGeometry

DetectionReviewStatus = Literal["pending", "confirmed", "rejected"]


class DetectionRequest(BaseModel):
    image_id: str = Field(min_length=1, max_length=64)


class DetectionUpdate(BaseModel):
    review_status: DetectionReviewStatus


class DetectionItem(BaseModel):
    id: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[int]
    estimated_location: PointGeometry
    review_status: DetectionReviewStatus

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: list[int]) -> list[int]:
        if len(value) != 4:
            raise ValueError("bbox must contain four integers")
        return value


class DetectionResponse(BaseModel):
    image_id: str
    detections: list[DetectionItem]
