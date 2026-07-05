from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_store
from app.schemas.annotations import AnnotationCreate, AnnotationResponse, AnnotationUpdate
from app.services.mock_data import AppStore

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.get("", response_model=list[AnnotationResponse])
def list_annotations(store: AppStore = Depends(get_store)):
    return store.list_annotations()


@router.post("", response_model=AnnotationResponse, status_code=201)
def create_annotation(payload: AnnotationCreate, store: AppStore = Depends(get_store)):
    return store.create_annotation(payload.model_dump())


@router.patch("/{annotation_id}", response_model=AnnotationResponse)
def update_annotation(
    annotation_id: str,
    payload: AnnotationUpdate,
    store: AppStore = Depends(get_store),
):
    annotation = store.update_annotation(annotation_id, payload.status)
    if annotation is None:
        raise HTTPException(status_code=404, detail=f"Annotation '{annotation_id}' was not found")
    return annotation
