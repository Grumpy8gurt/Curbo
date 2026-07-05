from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, field_validator

from app.schemas.geojson import PointGeometry

DetectionReviewStatus = Literal["pending", "confirmed", "rejected"]


class DetectionRequest(BaseModel):
    upload_id: str = Field(
        min_length=1,
        max_length=64,
        validation_alias=AliasChoices("upload_id", "image_id"),
    )


class DetectionUpdate(BaseModel):
    review_status: DetectionReviewStatus


class DetectionFeatureProperties(BaseModel):
    detection_id: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    review_status: DetectionReviewStatus
    source: str
    upload_id: str | None = None
    bbox: tuple[int, int, int, int] | None = None

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: tuple[int, int, int, int] | None) -> tuple[int, int, int, int] | None:
        if value is not None and len(value) != 4:
            raise ValueError("bbox must contain four integers")
        return value


class DetectionFeatureResponse(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: PointGeometry
    properties: DetectionFeatureProperties


class DetectionFeatureCollectionResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[DetectionFeatureResponse]


class DetectionItem(BaseModel):
    id: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[int]
    estimated_location: PointGeometry | None = None
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
