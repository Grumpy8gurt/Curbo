from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class UploadImageResponse(BaseModel):
    uploadId: str
    filename: str
    status: Literal["stored"]
