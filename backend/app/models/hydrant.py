from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Hydrant(Base):
    __tablename__ = "hydrants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    flow_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geometry: Mapped[dict] = mapped_column(JSON)
