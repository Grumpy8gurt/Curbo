from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class PointGeometry(BaseModel):
    """GeoJSON Point geometry.  Coordinates are [longitude, latitude] (x, y order)."""
    type: Literal["Point"] = "Point"
    coordinates: list[float]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, value: list[float]) -> list[float]:
        if len(value) != 2:
            raise ValueError("Point coordinates must contain longitude and latitude")
        return value


class LineStringGeometry(BaseModel):
    """GeoJSON LineString geometry.  At least two positions are required by the spec."""
    type: Literal["LineString"] = "LineString"
    coordinates: list[list[float]]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, value: list[list[float]]) -> list[list[float]]:
        if len(value) < 2:
            raise ValueError("LineString coordinates must contain at least two positions")
        if any(len(pair) != 2 for pair in value):
            raise ValueError("Each LineString coordinate must contain longitude and latitude")
        return value


class MultiLineStringGeometry(BaseModel):
    """
    GeoJSON MultiLineString geometry.  Used for road segments that were split
    across multiple line strings in the Eugene GIS export.
    No validator applied beyond Pydantic's structural check — the spatial query
    code handles both LineString and MultiLineString transparently.
    """
    type: Literal["MultiLineString"] = "MultiLineString"
    coordinates: list[list[list[float]]]


# Discriminated union of supported geometry types used in response schemas.
Geometry = PointGeometry | LineStringGeometry | MultiLineStringGeometry


class Feature(BaseModel):
    """Generic GeoJSON Feature.  id is optional per the GeoJSON spec (RFC 7946)."""
    type: Literal["Feature"] = "Feature"
    id: str | int | None = None
    geometry: Geometry
    properties: dict[str, Any] = Field(default_factory=dict)


class FeatureCollection(BaseModel):
    """
    GeoJSON FeatureCollection with an optional metadata extension.
    metadata is not part of the GeoJSON spec but is used throughout CURBO to
    carry layer status ("cached-eugene", "sample-fallback", "unavailable") and
    source attribution back to the frontend for display in the layer panel.
    """
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Feature] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None
