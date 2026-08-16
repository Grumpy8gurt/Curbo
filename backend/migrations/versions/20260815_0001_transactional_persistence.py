"""Create transactional annotation and report tables.

Revision ID: 20260815_0001
Revises:
Create Date: 2026-08-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260815_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "annotations",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("geometry", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'reviewed', 'confirmed', 'rejected')",
            name="ck_annotations_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_annotations_created_at", "annotations", ["created_at"])
    op.create_index("ix_annotations_status_created_at", "annotations", ["status", "created_at"])
    op.create_index("ix_annotations_type", "annotations", ["type"])

    op.create_table(
        "corridor_reports",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("road_id", sa.String(length=64), nullable=False),
        sa.Column("include_layers", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("download_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("format = 'html'", name="ck_corridor_reports_format"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_corridor_reports_created_at", "corridor_reports", ["created_at"])
    op.create_index("ix_corridor_reports_road_id", "corridor_reports", ["road_id"])


def downgrade() -> None:
    op.drop_index("ix_corridor_reports_road_id", table_name="corridor_reports")
    op.drop_index("ix_corridor_reports_created_at", table_name="corridor_reports")
    op.drop_table("corridor_reports")
    op.drop_index("ix_annotations_type", table_name="annotations")
    op.drop_index("ix_annotations_status_created_at", table_name="annotations")
    op.drop_index("ix_annotations_created_at", table_name="annotations")
    op.drop_table("annotations")
