from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_settings_from_request, get_store
from app.schemas.detections import (
    DetectionFeatureCollectionResponse,
    DetectionFeatureResponse,
    DetectionRequest,
    DetectionUpdate,
)
from app.services.detection_service import DetectionService
from app.services.mock_data import AppStore

router = APIRouter(tags=["detection"])


@router.get("/detection/curb-cuts", response_model=DetectionFeatureCollectionResponse)
def list_curb_cut_detections(store: AppStore = Depends(get_store)):
    return store.get_detections_feature_collection()


@router.post("/detection/curb-cuts", response_model=DetectionFeatureResponse)
def run_curb_cut_detection(
    payload: DetectionRequest,
    store: AppStore = Depends(get_store),
    settings=Depends(get_settings_from_request),
):
    image_record = store.get_upload(payload.upload_id)
    if image_record is None:
        raise HTTPException(status_code=404, detail=f"Upload '{payload.upload_id}' was not found")
    detections = DetectionService(settings.ml_service_url).run_curb_cut_detection(image_record)
    stored_detections = store.add_detections(payload.upload_id, detections)
    return store.detection_to_feature(stored_detections[0])


@router.patch("/detection/{detection_id}", response_model=DetectionFeatureResponse)
@router.patch("/detections/{detection_id}", response_model=DetectionFeatureResponse)
def update_detection(
    detection_id: str,
    payload: DetectionUpdate,
    store: AppStore = Depends(get_store),
):
    detection = store.update_detection(detection_id, payload.review_status)
    if detection is None:
        raise HTTPException(status_code=404, detail=f"Detection '{detection_id}' was not found")
    return store.detection_to_feature(detection)
