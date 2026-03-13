from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BIGINT_ID, Base, TimestampMixin


class AiAnalysis(TimestampMixin, Base):
    __tablename__ = "xc_ai_analysis"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    ref_id: Mapped[int] = mapped_column(BIGINT_ID, nullable=False, index=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(50))
    provider: Mapped[Optional[str]] = mapped_column(String(20))
    prompt_version: Mapped[Optional[str]] = mapped_column(String(20))
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    provider_errors: Mapped[list[str] | None] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=2, nullable=False)


class AiPromptTemplate(TimestampMixin, Base):
    __tablename__ = "xc_ai_prompt_template"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    template_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    scene: Mapped[str] = mapped_column(String(30), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_tpl: Mapped[str] = mapped_column(Text, nullable=False)
    model_tier: Mapped[str] = mapped_column(String(10), default="PRO", nullable=False)
    temperature: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0.70, nullable=False
    )
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
