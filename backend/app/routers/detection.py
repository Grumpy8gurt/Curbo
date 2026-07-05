from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_store
from app.schemas.detections import DetectionItem, DetectionRequest, DetectionResponse, DetectionUpdate
from app.services.detection_service import DetectionService
from app.services.mock_data import AppStore

router = APIRouter(prefix="/detection", tags=["detection"])


@router.post("/curb-cuts", response_model=DetectionResponse)
def run_curb_cut_detection(
    payload: DetectionRequest,
    store: AppStore = Depends(get_store),
):
    image_record = store.get_upload(payload.image_id)
    if image_record is None:
        raise HTTPException(status_code=404, detail=f"Image '{payload.image_id}' was not found")
    detections = DetectionService().run_curb_cut_detection(image_record)
    stored_detections = store.add_detections(payload.image_id, detections)
    return {"image_id": payload.image_id, "detections": stored_detections}


@router.patch("/{detection_id}", response_model=DetectionItem)
def update_detection(
    detection_id: str,
    payload: DetectionUpdate,
    store: AppStore = Depends(get_store),
):
    detection = store.update_detection(detection_id, payload.review_status)
    if detection is None:
        raise HTTPException(status_code=404, detail=f"Detection '{detection_id}' was not found")
    return detection
