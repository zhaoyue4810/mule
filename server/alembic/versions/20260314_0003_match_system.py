"""match system

Revision ID: 20260314_0003
Revises: 20260313_0002
Create Date: 2026-03-14 21:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260314_0003"
down_revision = "20260313_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "xc_match_session",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("initiator_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("partner_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="SET NULL"), nullable=True),
        sa.Column("test_id", sa.BigInteger(), sa.ForeignKey("xc_test.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="WAITING"),
        sa.Column("invite_code", sa.String(length=20), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_xc_match_session_initiator", "xc_match_session", ["initiator_id"])
    op.create_index("idx_xc_match_session_partner", "xc_match_session", ["partner_id"])
    op.create_index("idx_xc_match_session_test", "xc_match_session", ["test_id"])

    op.create_table(
        "xc_match_report",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("xc_match_session.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("initiator_report_id", sa.BigInteger(), sa.ForeignKey("xc_test_record.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("partner_report_id", sa.BigInteger(), sa.ForeignKey("xc_test_record.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("compatibility_score", sa.Integer(), nullable=False),
        sa.Column("dimension_comparison", sa.JSON(), nullable=False),
        sa.Column("analysis", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_xc_match_report_session", "xc_match_report", ["session_id"])


def downgrade() -> None:
    op.drop_index("idx_xc_match_report_session", table_name="xc_match_report")
    op.drop_table("xc_match_report")
    op.drop_index("idx_xc_match_session_test", table_name="xc_match_session")
    op.drop_index("idx_xc_match_session_partner", table_name="xc_match_session")
    op.drop_index("idx_xc_match_session_initiator", table_name="xc_match_session")
    op.drop_table("xc_match_session")
