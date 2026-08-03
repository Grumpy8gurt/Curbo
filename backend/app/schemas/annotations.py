from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.schemas.geojson import LineStringGeometry, PointGeometry

# Allowed values for the discriminated annotation_type field.
# "missing curb cut" is the primary use case; the others cover edge cases
# encountered during field review.
AnnotationType = Literal[
    "curb cut",
    "missing curb cut",
    "fire hydrant",
    "bike lane gap",
    "proposed bike lane",
    "obstruction",
    "parking/loading conflict",
    "intersection safety",
    "drainage/utility conflict",
    "bad data",
    "other",
]

AnnotationGeometry = PointGeometry | LineStringGeometry

# Lifecycle states an annotation can move through:
#   pending → reviewed → confirmed | rejected
AnnotationStatus = Literal["pending", "reviewed", "confirmed", "rejected"]


class AnnotationCreate(BaseModel):
    annotation_type: AnnotationType = Field(
        # Accept camelCase (frontend), snake_case (API docs), and short alias
        # so both the frontend JSON body and curl examples work without a transformer.
        validation_alias=AliasChoices("annotationType", "annotation_type", "type")
    )
    description: str = Field(min_length=1, max_length=2000)
    # Convenience fields — the frontend sends lat/lng directly to avoid
    # constructing a GeoJSON geometry object in JavaScript.
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    # If geometry is provided explicitly it takes precedence over lat/lng.
    geometry: AnnotationGeometry | None = None
    source: str = Field(default="planner", min_length=1, max_length=64)

    @model_validator(mode="after")
    def populate_geometry(self) -> "AnnotationCreate":
        """
        Ensure geometry is always populated after validation.
        If geometry was not provided directly, build it from the lat/lng
        convenience fields.  Note GeoJSON coordinate order is [lng, lat].
        Raises ValueError (converted to HTTP 422) when neither geometry nor
        both lat/lng are provided.
        """
        if self.geometry is None:
            if self.latitude is None or self.longitude is None:
                raise ValueError("latitude and longitude are required when geometry is omitted")
            self.geometry = PointGeometry(coordinates=[self.longitude, self.latitude])
        return self


class AnnotationUpdate(BaseModel):
    """Partial update — only status transitions are supported post-creation."""
    status: AnnotationStatus


class AnnotationFeatureProperties(BaseModel):
    annotation_id: str
    annotation_type: AnnotationType
    description: str
    status: AnnotationStatus
    source: str
    created_at: datetime


class AnnotationFeatureResponse(BaseModel):
    """GeoJSON Feature shape returned by POST /annotations and PATCH /annotations/{id}."""
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: AnnotationGeometry
    properties: AnnotationFeatureProperties


class AnnotationFeatureCollectionResponse(BaseModel):
    """GeoJSON FeatureCollection returned by GET /annotations."""
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[AnnotationFeatureResponse]
