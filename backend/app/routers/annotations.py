from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_store
from app.schemas.annotations import (
    AnnotationCreate,
    AnnotationFeatureCollectionResponse,
    AnnotationFeatureResponse,
    AnnotationUpdate,
)
from app.services.app_store import AppStore

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.get("", response_model=AnnotationFeatureCollectionResponse)
def list_annotations(store: AppStore = Depends(get_store)):
    """Return all planner annotations sorted by creation time."""
    return store.get_annotations_feature_collection()


@router.post("", response_model=AnnotationFeatureResponse, status_code=201)
def create_annotation(payload: AnnotationCreate, store: AppStore = Depends(get_store)):
    """
    Create a new planner annotation.

    The payload supports two geometry formats:
      - Explicit GeoJSON PointGeometry via the `geometry` field.
      - Convenience `latitude` / `longitude` fields, which the schema validator
        converts to a PointGeometry automatically.

    The response is a GeoJSON Feature so the frontend can push it directly into
    the annotations layer without a separate GET.
    """
    annotation = store.create_annotation(
        {
            "annotation_type": payload.annotation_type,
            "description": payload.description,
            "geometry": payload.geometry.model_dump(),
            "source": payload.source,
        }
    )
    return store.annotation_to_feature(annotation)


@router.patch("/{annotation_id}", response_model=AnnotationFeatureResponse)
def update_annotation(
    annotation_id: str,
    payload: AnnotationUpdate,
    store: AppStore = Depends(get_store),
):
    """
    Update the review status of an existing annotation.
    Only `status` can be changed — annotation_type and geometry are immutable
    after creation to preserve field-review provenance.
    """
    annotation = store.update_annotation(annotation_id, payload.status)
    if annotation is None:
        raise HTTPException(status_code=404, detail=f"Annotation '{annotation_id}' was not found")
    return store.annotation_to_feature(annotation)
