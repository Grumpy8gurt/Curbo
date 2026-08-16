from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, CheckConstraint, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CorridorReport(Base):
    __tablename__ = "corridor_reports"
    __table_args__ = (
        CheckConstraint("format = 'html'", name="ck_corridor_reports_format"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    road_id: Mapped[str] = mapped_column(String(64), index=True)
    include_layers: Mapped[list[str]] = mapped_column(JSON)
    summary: Mapped[dict] = mapped_column(JSON)
    format: Mapped[str] = mapped_column(String(16), default="html")
    download_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
