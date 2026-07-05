from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.dependencies import get_settings_from_request, get_store
from app.schemas.uploads import UploadImageResponse
from app.services.mock_data import AppStore

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/images", response_model=UploadImageResponse, status_code=201)
async def upload_image(
    file: UploadFile | None = File(default=None),
    image: UploadFile | None = File(default=None),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    road_id: str | None = Form(default=None),
    note: str | None = Form(default=None),
    store: AppStore = Depends(get_store),
    settings=Depends(get_settings_from_request),
):
    upload_file = image or file
    if upload_file is None:
        raise HTTPException(status_code=422, detail="An image file is required")

    image_record = store.create_upload(
        {
            "filename": upload_file.filename,
            "file_path": "",
            "latitude": latitude,
            "longitude": longitude,
            "road_id": road_id,
            "note": note,
        }
    )
    suffix = Path(upload_file.filename or "upload.bin").suffix or ".bin"
    destination = settings.resolved_upload_dir / f"{image_record['id']}{suffix}"
    file_bytes = await upload_file.read()
    destination.write_bytes(file_bytes)
    image_record["file_path"] = str(destination)
    await upload_file.close()
    return {
        "uploadId": image_record["id"],
        "filename": image_record["filename"],
        "status": "stored",
    }
