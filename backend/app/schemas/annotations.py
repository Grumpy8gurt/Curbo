from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.geojson import PointGeometry

AnnotationType = Literal[
    "missing_curb_cut",
    "obstruction",
    "note",
    "hydrant_conflict",
    "parking_conflict",
]
AnnotationStatus = Literal["pending", "confirmed", "rejected"]


class AnnotationCreate(BaseModel):
    type: AnnotationType
    description: str = Field(min_length=1, max_length=2000)
    geometry: PointGeometry
    source: str = Field(default="field_survey", min_length=1, max_length=64)


class AnnotationUpdate(BaseModel):
    status: AnnotationStatus


class AnnotationResponse(BaseModel):
    id: str
    type: AnnotationType
    description: str
    status: AnnotationStatus
    source: str
    geometry: PointGeometry
    created_at: datetime
