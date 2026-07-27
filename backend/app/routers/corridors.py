from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_store
from app.schemas.corridors import CorridorAnalysisRequest, CorridorAnalysisResponse
from app.services.app_store import AppStore
from app.services.spatial_queries import analyze_corridor

router = APIRouter(prefix="/corridors", tags=["corridors"])


@router.post("/analyze", response_model=CorridorAnalysisResponse)
def analyze_corridor_route(
    payload: CorridorAnalysisRequest,
    store: AppStore = Depends(get_store),
):
    """
    Analyse a road corridor and return a planning summary.

    POST is used rather than GET because the payload may grow to include
    additional filter options (layer masks, custom buffer sizes) in future
    sprints.  buffer_meters defaults to 30 m but is configurable per-request
    within the 0–500 m range defined in the schema.
    """
    return analyze_corridor(store, payload.road_id, payload.buffer_meters)
