"""add p2 time capsule fields

Revision ID: 20260314_0004
Revises: 20260314_0003
Create Date: 2026-03-14 18:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260314_0004"
down_revision = "20260314_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("xc_time_capsule", sa.Column("persona_title", sa.String(length=100), nullable=True))
    op.add_column("xc_time_capsule", sa.Column("persona_icon", sa.String(length=10), nullable=True))
    op.add_column(
        "xc_time_capsule",
        sa.Column("test_id", sa.BigInteger(), sa.ForeignKey("xc_test.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "xc_time_capsule",
        sa.Column(
            "report_id",
            sa.BigInteger(),
            sa.ForeignKey("xc_report_snapshot.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "xc_time_capsule",
        sa.Column("duration_days", sa.Integer(), nullable=True),
    )

    op.execute("UPDATE xc_time_capsule SET persona_title = persona_name WHERE persona_title IS NULL")
    op.execute("UPDATE xc_time_capsule SET persona_icon = persona_emoji WHERE persona_icon IS NULL")
    op.execute("UPDATE xc_time_capsule SET duration_days = lock_days WHERE duration_days IS NULL")

    op.alter_column("xc_time_capsule", "duration_days", nullable=False)


def downgrade() -> None:
    op.drop_column("xc_time_capsule", "duration_days")
    op.drop_column("xc_time_capsule", "report_id")
    op.drop_column("xc_time_capsule", "test_id")
    op.drop_column("xc_time_capsule", "persona_icon")
    op.drop_column("xc_time_capsule", "persona_title")
