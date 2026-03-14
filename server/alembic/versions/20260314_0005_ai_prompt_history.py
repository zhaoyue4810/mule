"""add ai prompt template history

Revision ID: 20260314_0005
Revises: 20260314_0004
Create Date: 2026-03-14 20:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260314_0005"
down_revision = "20260314_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "xc_ai_prompt_template_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("template_id", sa.BigInteger(), nullable=False),
        sa.Column("template_code", sa.String(length=50), nullable=False),
        sa.Column("scene", sa.String(length=30), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("user_prompt_tpl", sa.Text(), nullable=False),
        sa.Column("model_tier", sa.String(length=10), nullable=False, server_default="PRO"),
        sa.Column("temperature", sa.Numeric(3, 2), nullable=False, server_default="0.70"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "idx_xc_ai_prompt_template_history_template",
        "xc_ai_prompt_template_history",
        ["template_id", "version"],
    )


def downgrade() -> None:
    op.drop_index("idx_xc_ai_prompt_template_history_template", table_name="xc_ai_prompt_template_history")
    op.drop_table("xc_ai_prompt_template_history")
