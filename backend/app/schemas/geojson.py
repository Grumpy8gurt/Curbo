from __future__ import annotations

from typing import Any, Literal

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


class LineStringGeometry(BaseModel):
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
    type: Literal["MultiLineString"] = "MultiLineString"
    coordinates: list[list[list[float]]]


Geometry = PointGeometry | LineStringGeometry | MultiLineStringGeometry


class Feature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str | int | None = None
    geometry: Geometry
    properties: dict[str, Any] = Field(default_factory=dict)


class FeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[Feature] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None
