from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BIGINT_ID, Base, TimestampMixin


class MatchSession(TimestampMixin, Base):
    __tablename__ = "xc_match_session"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    initiator_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_user.id", ondelete="CASCADE"),
        nullable=False,
    )
    partner_id: Mapped[Optional[int]] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_user.id", ondelete="SET NULL"),
    )
    test_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_test.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), default="WAITING", nullable=False)
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class MatchReport(TimestampMixin, Base):
    __tablename__ = "xc_match_report"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_match_session.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    initiator_report_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_test_record.id", ondelete="RESTRICT"),
        nullable=False,
    )
    partner_report_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_test_record.id", ondelete="RESTRICT"),
        nullable=False,
    )
    compatibility_score: Mapped[int] = mapped_column(Integer, nullable=False)
    dimension_comparison: Mapped[dict] = mapped_column(JSON, nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
