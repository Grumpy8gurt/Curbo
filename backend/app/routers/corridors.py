from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_store
from app.schemas.corridors import CorridorAnalysisRequest, CorridorAnalysisResponse
from app.services.mock_data import AppStore
from app.services.spatial_queries import analyze_corridor

router = APIRouter(prefix="/corridors", tags=["corridors"])


@router.post("/analyze", response_model=CorridorAnalysisResponse)
def analyze_corridor_route(
    payload: CorridorAnalysisRequest,
    store: AppStore = Depends(get_store),
):
    return analyze_corridor(store, payload.road_id, payload.buffer_meters)
