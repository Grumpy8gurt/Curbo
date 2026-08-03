from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.dependencies import get_settings_from_request, get_store
from app.schemas.reports import CorridorReportRequest, CorridorReportResponse
from app.services.app_store import AppStore
from app.services.report_generator import generate_corridor_report
from app.services.spatial_queries import analyze_corridor

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/corridor", response_model=CorridorReportResponse, status_code=201)
def create_corridor_report(
    payload: CorridorReportRequest,
    store: AppStore = Depends(get_store),
    settings=Depends(get_settings_from_request),
):
    """
    Generate an HTML corridor report and register it in the store.

    The corridor analysis is re-run with a fixed 30 m buffer rather than
    reading a previously cached result so that the report always reflects the
    current annotation state.

    The returned downloadUrl points to the GET /{report_id}/download endpoint
    which serves the file as a FileResponse.  Reports are not persisted across
    restarts — only the HTML file on disk remains.
    """
    analysis = analyze_corridor(store, payload.road_id, buffer_meters=30)
    summary_message = (
        f"{analysis.name} corridor report queued successfully. "
        "Export includes Eugene layer counts, planning notes, and annotation status."
    )
    report_id = store.next_id("report")
    report_path = generate_corridor_report(
        settings.resolved_report_dir,
        report_id=report_id,
        summary=analysis.model_dump(),
        include_layers=["roads", "sidewalkRamps", "hydrants", "bikeLanes", "annotations"],
    )
    store.create_report(
        {
            "id": report_id,
            "road_id": payload.road_id,
            "format": payload.format,
            "summary": summary_message,
            "download_path": str(report_path),
        }
    )
    return {
        "reportId": report_id,
        "roadId": payload.road_id,
        "downloadUrl": f"/api/reports/{report_id}/download",
        "summary": summary_message,
    }


@router.get("/{report_id}/download")
def download_report(report_id: str, store: AppStore = Depends(get_store)):
    """
    Serve a previously generated HTML report as a file download.
    Reports are looked up by ID in the in-memory store; the store is seeded on
    startup so only reports generated in the current process lifetime are
    available.
    """
    report = store.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' was not found")
    return FileResponse(report["download_path"], filename=f"{report_id}.html", media_type="text/html")
