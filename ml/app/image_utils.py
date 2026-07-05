from __future__ import annotations

from io import BytesIO
from typing import Any

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
    "image/tiff",
}


async def read_image_metadata(file: UploadFile) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="An image filename is required")

    content_type = file.content_type or ""
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    try:
        with Image.open(BytesIO(raw_bytes)) as image:
            image.verify()
        with Image.open(BytesIO(raw_bytes)) as image:
            width, height = image.size
            image_format = image.format
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Unsupported or unreadable image file") from exc
    except OSError as exc:
        raise HTTPException(status_code=400, detail="Unsupported or unreadable image file") from exc

    if width <= 0 or height <= 0:
        raise HTTPException(status_code=400, detail="Image dimensions must be greater than zero")

    await file.seek(0)
    return {"width": width, "height": height, "format": image_format, "content_type": content_type}
