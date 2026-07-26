from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CorridorReport(Base):
    __tablename__ = "corridor_reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    road_id: Mapped[str] = mapped_column(String(64), index=True)
    include_layers: Mapped[list[str]] = mapped_column(JSON)
    summary: Mapped[dict] = mapped_column(JSON)
    download_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
