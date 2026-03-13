from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BIGINT_ID, Base, TimestampMixin


class ReportSnapshot(TimestampMixin, Base):
    __tablename__ = "xc_report_snapshot"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_test_record.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    dimension_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    overall_score: Mapped[Optional[int]] = mapped_column(Integer)
    persona_code: Mapped[Optional[str]] = mapped_column(String(50))
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    ai_text: Mapped[Optional[str]] = mapped_column(Text)
    share_card_url: Mapped[Optional[str]] = mapped_column(String(500))
