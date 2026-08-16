from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from app.dependencies import get_settings_from_request, get_store
from app.schemas.annotations import (
    AnnotationCreate,
    AnnotationFeatureCollectionResponse,
    AnnotationFeatureResponse,
    AnnotationUpdate,
)
from app.services.app_store import (
    AppStore,
    ConcurrencyConflictError,
    InvalidTransitionError,
)

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.get("", response_model=AnnotationFeatureCollectionResponse)
def list_annotations(store: AppStore = Depends(get_store)):
    """Return all planner annotations sorted by creation time."""
    return store.get_annotations_feature_collection()


@router.post("", response_model=AnnotationFeatureResponse, status_code=201)
def create_annotation(
    payload: AnnotationCreate,
    store: AppStore = Depends(get_store),
    settings=Depends(get_settings_from_request),
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", min_length=8, max_length=128
    ),
):
    """
    Create a new planner annotation.

    The payload supports two geometry formats:
      - Explicit GeoJSON Point or LineString via the `geometry` field.
      - Convenience `latitude` / `longitude` fields, which the schema validator
        converts to a Point automatically.

    The response is a GeoJSON Feature so the frontend can push it directly into
    the annotations layer without a separate GET.
    """
    if settings.auth_required and idempotency_key is None:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key is required for authenticated annotation creation",
        )
    annotation = store.create_annotation(
        {
            "annotation_type": payload.annotation_type,
            "description": payload.description,
            "geometry": payload.geometry.model_dump(),
            "source": "authenticated reviewer" if settings.auth_required else "local reviewer",
        },
        idempotency_key=idempotency_key,
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
    try:
        annotation = store.update_annotation(
            annotation_id,
            payload.status,
            expected_version=payload.expected_version,
        )
    except ConcurrencyConflictError:
        raise HTTPException(
            status_code=409,
            detail="Annotation changed since it was loaded; refresh and try again",
        ) from None
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    if annotation is None:
        raise HTTPException(status_code=404, detail=f"Annotation '{annotation_id}' was not found")
    return store.annotation_to_feature(annotation)
