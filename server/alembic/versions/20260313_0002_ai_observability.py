"""add ai observability fields

Revision ID: 20260313_0002
Revises: 20260313_0001
Create Date: 2026-03-13 23:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260313_0002"
down_revision = "20260313_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("xc_ai_analysis", sa.Column("provider_errors", sa.JSON(), nullable=True))
    op.add_column("xc_ai_analysis", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column(
        "xc_ai_analysis",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "xc_ai_analysis",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("xc_ai_analysis", "completed_at")
    op.drop_column("xc_ai_analysis", "started_at")
    op.drop_column("xc_ai_analysis", "error_message")
    op.drop_column("xc_ai_analysis", "provider_errors")
