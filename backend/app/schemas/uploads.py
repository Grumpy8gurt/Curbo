from __future__ import annotations

from pydantic import BaseModel


class UploadImageResponse(BaseModel):
    image_id: str
    filename: str
    status: str
