from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.dependencies import get_settings_from_request, get_store
from app.schemas.reports import CorridorReportRequest, CorridorReportResponse
from app.services.app_store import AppStore
from app.services.report_generator import generate_corridor_report, prune_reports
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

    The returned downloadUrl points to the GET /{report_id}/download endpoint.
    Database metadata is used when configured, and the retained HTML artifact
    also supports safe local-development downloads after a restart.
    """
    analysis = analyze_corridor(store, payload.road_id, buffer_meters=30)
    summary_message = (
        f"{analysis.name} corridor report generated successfully. "
        "Export includes Eugene layer counts, planning notes, and annotation status."
    )
    report_id = store.next_id("report")
    prune_reports(
        settings.resolved_report_dir,
        retention_days=settings.report_retention_days,
        max_files=max(settings.max_report_files - 1, 0),
    )
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
            "include_layers": ["roads", "sidewalkRamps", "hydrants", "bikeLanes", "annotations"],
            "download_path": str(report_path),
        }
    )
    return {
        "reportId": report_id,
        "roadId": payload.road_id,
        "downloadUrl": f"/api/v1/reports/{report_id}/download",
        "summary": summary_message,
    }


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    store: AppStore = Depends(get_store),
    settings=Depends(get_settings_from_request),
):
    """
    Serve a previously generated HTML report as a file download.
    Reports are looked up through durable metadata when configured. In local
    development, a correctly formed report ID may resolve to its retained HTML
    file inside the configured report directory after a restart.
    """
    report = store.get_report(report_id)
    if report is None:
        if not re.fullmatch(r"rep_[0-9a-f]{32}", report_id):
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' was not found")
        durable_path = settings.resolved_report_dir / f"{report_id}.html"
        if not durable_path.is_file():
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' was not found")
        download_path = durable_path
    else:
        download_path = Path(report["download_path"])
    download_path = Path(download_path).resolve()
    report_root = settings.resolved_report_dir.resolve()
    if download_path.parent != report_root or not download_path.is_file():
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' was not found")
    return FileResponse(download_path, filename=f"{report_id}.html", media_type="text/html")
