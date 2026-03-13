"""initial schema

Revision ID: 20260313_0001
Revises:
Create Date: 2026-03-13 18:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260313_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "xc_user",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("openid", sa.String(length=64), nullable=True, unique=True),
        sa.Column("unionid", sa.String(length=64), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("nickname", sa.String(length=50), nullable=False, server_default="探索者"),
        sa.Column("avatar_type", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("avatar_value", sa.String(length=255), nullable=False, server_default="🧠"),
        sa.Column("bio", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("gender", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("birth_month", sa.Integer(), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sound_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_xc_user_phone", "xc_user", ["phone"])

    op.create_table(
        "xc_user_setting",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("notif_match", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notif_result", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notif_friend", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notif_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("privacy_show_profile", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("privacy_show_history", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("privacy_allow_match", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("privacy_anonymous", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "xc_user_memory",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("test_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_duration", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fav_categories", sa.JSON(), nullable=True),
        sa.Column("know_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "xc_test",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("test_code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=True),
        sa.Column("is_match_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("participant_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("yaml_source", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_xc_test_category", "xc_test", ["category"])

    op.create_table(
        "xc_test_version",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("test_id", sa.BigInteger(), sa.ForeignKey("xc_test.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("duration_hint", sa.String(length=20), nullable=True),
        sa.Column("cover_gradient", sa.String(length=200), nullable=True),
        sa.Column("report_template_code", sa.String(length=50), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("test_id", "version", name="uq_xc_test_version_test_id"),
    )
    op.create_index("idx_xc_test_version_status", "xc_test_version", ["status"])

    op.create_table(
        "xc_dimension",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("version_id", sa.BigInteger(), sa.ForeignKey("xc_test_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dim_code", sa.String(length=50), nullable=False),
        sa.Column("dim_name", sa.String(length=50), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("idx_xc_dimension_version", "xc_dimension", ["version_id"])

    op.create_table(
        "xc_question",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("version_id", sa.BigInteger(), sa.ForeignKey("xc_test_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_code", sa.String(length=50), nullable=True),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.String(length=500), nullable=False),
        sa.Column("interaction_type", sa.String(length=20), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("dim_weights", sa.JSON(), nullable=False),
    )
    op.create_index("idx_xc_question_version_seq", "xc_question", ["version_id", "seq"])

    op.create_table(
        "xc_option",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("xc_question.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_code", sa.String(length=20), nullable=True),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("score_rules", sa.JSON(), nullable=True),
        sa.Column("ext_config", sa.JSON(), nullable=True),
    )
    op.create_index("idx_xc_option_question", "xc_option", ["question_id"])

    op.create_table(
        "xc_test_persona",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("version_id", sa.BigInteger(), sa.ForeignKey("xc_test_version.id", ondelete="CASCADE"), nullable=False),
        sa.Column("persona_key", sa.String(length=50), nullable=False),
        sa.Column("persona_name", sa.String(length=100), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=True),
        sa.Column("rarity_percent", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("soul_signature", sa.String(length=200), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("dim_pattern", sa.JSON(), nullable=False),
        sa.Column("capsule_prompt", sa.String(length=300), nullable=True),
    )
    op.create_index("idx_xc_test_persona_version", "xc_test_persona", ["version_id"])

    op.create_table(
        "xc_test_record",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_id", sa.BigInteger(), sa.ForeignKey("xc_test.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_id", sa.BigInteger(), sa.ForeignKey("xc_test_version.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("persona_id", sa.BigInteger(), sa.ForeignKey("xc_test_persona.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scores", sa.JSON(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_xc_test_record_user_time", "xc_test_record", ["user_id", "created_at"])
    op.create_index("idx_xc_test_record_test", "xc_test_record", ["test_id"])

    op.create_table(
        "xc_test_answer",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("record_id", sa.BigInteger(), sa.ForeignKey("xc_test_record.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("xc_question.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("answer_value", sa.JSON(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_xc_test_answer_record", "xc_test_answer", ["record_id"])

    op.create_table(
        "xc_report_snapshot",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("record_id", sa.BigInteger(), sa.ForeignKey("xc_test_record.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("dimension_scores", sa.JSON(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("persona_code", sa.String(length=50), nullable=True),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("ai_text", sa.Text(), nullable=True),
        sa.Column("share_card_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "xc_ai_analysis",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("ref_id", sa.BigInteger(), nullable=False),
        sa.Column("model_used", sa.String(length=50), nullable=True),
        sa.Column("provider", sa.String(length=20), nullable=True),
        sa.Column("prompt_version", sa.String(length=20), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="2"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_xc_ai_analysis_ref", "xc_ai_analysis", ["type", "ref_id"])

    op.create_table(
        "xc_badge_definition",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("badge_key", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("unlock_rule", sa.JSON(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("yaml_source", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "xc_user_badge",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("badge_id", sa.BigInteger(), sa.ForeignKey("xc_badge_definition.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tier", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("unlock_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_xc_user_badge_user", "xc_user_badge", ["user_id"])

    op.create_table(
        "xc_calendar_entry",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("mood_level", sa.SmallInteger(), nullable=True),
        sa.Column("test_record_id", sa.BigInteger(), sa.ForeignKey("xc_test_record.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="manual"),
    )

    op.create_table(
        "xc_daily_soul_question",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("question_text", sa.String(length=300), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("insights", sa.JSON(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("yaml_source", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "xc_daily_soul_answer",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("xc_daily_soul_question.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer_index", sa.SmallInteger(), nullable=False),
        sa.Column("answer_date", sa.Date(), nullable=False),
    )

    op.create_table(
        "xc_time_capsule",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("persona_name", sa.String(length=100), nullable=True),
        sa.Column("persona_emoji", sa.String(length=10), nullable=True),
        sa.Column("lock_days", sa.Integer(), nullable=False),
        sa.Column("unlock_date", sa.Date(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_xc_time_capsule_unlock", "xc_time_capsule", ["unlock_date", "is_read"])

    op.create_table(
        "xc_soul_fragment_definition",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("fragment_key", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=True),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("required_test_code", sa.String(length=50), nullable=True),
        sa.Column("insight", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("yaml_source", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "xc_user_soul_fragment",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fragment_id", sa.BigInteger(), sa.ForeignKey("xc_soul_fragment_definition.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "xc_import_task",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("file_type", sa.String(length=10), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("parse_log", sa.Text(), nullable=True),
        sa.Column("ai_log", sa.Text(), nullable=True),
        sa.Column("preview_json", sa.JSON(), nullable=True),
        sa.Column("operator_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "xc_ai_prompt_template",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("template_code", sa.String(length=50), nullable=False, unique=True),
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


def downgrade() -> None:
    for table_name in [
        "xc_ai_prompt_template",
        "xc_import_task",
        "xc_user_soul_fragment",
        "xc_soul_fragment_definition",
        "xc_time_capsule",
        "xc_daily_soul_answer",
        "xc_daily_soul_question",
        "xc_calendar_entry",
        "xc_user_badge",
        "xc_badge_definition",
        "xc_ai_analysis",
        "xc_report_snapshot",
        "xc_test_answer",
        "xc_test_record",
        "xc_test_persona",
        "xc_option",
        "xc_question",
        "xc_dimension",
        "xc_test_version",
        "xc_test",
        "xc_user_memory",
        "xc_user_setting",
        "xc_user",
    ]:
        op.drop_table(table_name)
