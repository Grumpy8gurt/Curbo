from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_store
from app.schemas.layers import LayerFeatureCollection
from app.services.mock_data import AppStore
from app.services.spatial_queries import filter_feature_collection, parse_bbox

router = APIRouter(prefix="/layers", tags=["layers"])


@router.get("/roads", response_model=LayerFeatureCollection)
def get_roads(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    return filter_feature_collection(store.roads, parse_bbox(bbox))


@router.get("/curb-ramps", response_model=LayerFeatureCollection)
def get_curb_ramps(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    return filter_feature_collection(store.curb_ramps, parse_bbox(bbox))


@router.get("/hydrants", response_model=LayerFeatureCollection)
def get_hydrants(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    return filter_feature_collection(store.hydrants, parse_bbox(bbox))


@router.get("/annotations", response_model=LayerFeatureCollection)
def get_annotation_layer(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    return filter_feature_collection(store.get_annotations_feature_collection(), parse_bbox(bbox))


@router.get("/detections", response_model=LayerFeatureCollection)
def get_detection_layer(
    bbox: str | None = Query(default=None),
    store: AppStore = Depends(get_store),
):
    return filter_feature_collection(store.get_detections_feature_collection(), parse_bbox(bbox))
