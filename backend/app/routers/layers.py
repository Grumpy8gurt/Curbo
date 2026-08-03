from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_store
from app.schemas.layers import LayerFeatureCollection
from app.services.app_store import AppStore
from app.services.spatial_queries import filter_feature_collection, parse_bbox

router = APIRouter(prefix="/layers", tags=["layers"])


@router.get("/roads", response_model=LayerFeatureCollection)
def get_roads(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    """Return the full road network, optionally clipped to a bounding box."""
    return filter_feature_collection(store.roads, parse_bbox(bbox))


def _get_sidewalk_ramps(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    """Shared implementation used by both the canonical and alias endpoints."""
    return filter_feature_collection(store.curb_ramps, parse_bbox(bbox))


@router.get("/sidewalk-ramps", response_model=LayerFeatureCollection)
def get_sidewalk_ramps(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    """Return sidewalk ramp / curb ramp point features."""
    return _get_sidewalk_ramps(bbox, store)


@router.get("/curb-ramps", response_model=LayerFeatureCollection)
def get_curb_ramps_alias(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    """
    Alias for /sidewalk-ramps retained for frontend compatibility.
    Both endpoints serve the same curb_ramps collection from the store.
    """
    return _get_sidewalk_ramps(bbox, store)


@router.get("/hydrants", response_model=LayerFeatureCollection)
def get_hydrants(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    """Return fire hydrant point features."""
    return filter_feature_collection(store.hydrants, parse_bbox(bbox))


@router.get("/bike-lanes", response_model=LayerFeatureCollection)
def get_bike_lanes(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    """Return bicycle facility line features."""
    return filter_feature_collection(store.bike_lanes, parse_bbox(bbox))


@router.get("/annotations", response_model=LayerFeatureCollection)
def get_annotation_layer(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    """
    Return planner annotations as a GeoJSON layer (same format as other layers
    so the frontend can render them identically in MapLibre).
    A bbox filter here is useful for tile-based queries in a future map client.
    """
    return filter_feature_collection(store.get_annotations_feature_collection(), parse_bbox(bbox))
