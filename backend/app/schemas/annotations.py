from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.schemas.geojson import PointGeometry

AnnotationType = Literal["missing curb cut", "bad data", "obstruction", "other"]
AnnotationStatus = Literal["pending", "reviewed", "confirmed", "rejected"]


class AnnotationCreate(BaseModel):
    annotation_type: AnnotationType = Field(
        validation_alias=AliasChoices("annotationType", "annotation_type", "type")
    )
    description: str = Field(min_length=1, max_length=2000)
    latitude: float | None = None
    longitude: float | None = None
    geometry: PointGeometry | None = None
    source: str = Field(default="planner", min_length=1, max_length=64)

    @model_validator(mode="after")
    def populate_geometry(self) -> "AnnotationCreate":
        if self.geometry is None:
            if self.latitude is None or self.longitude is None:
                raise ValueError("latitude and longitude are required when geometry is omitted")
            self.geometry = PointGeometry(coordinates=[self.longitude, self.latitude])
        return self


class AnnotationUpdate(BaseModel):
    status: AnnotationStatus


class AnnotationFeatureProperties(BaseModel):
    annotation_id: str
    annotation_type: AnnotationType
    description: str
    status: AnnotationStatus
    source: str
    created_at: datetime


class AnnotationFeatureResponse(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: PointGeometry
    properties: AnnotationFeatureProperties


class AnnotationFeatureCollectionResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[AnnotationFeatureResponse]
