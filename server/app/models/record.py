from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BIGINT_ID, Base, TimestampMixin


class TestRecord(TimestampMixin, Base):
    __tablename__ = "xc_test_record"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False
    )
    test_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_test.id", ondelete="CASCADE"), nullable=False
    )
    version_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_test_version.id", ondelete="RESTRICT"), nullable=False
    )
    persona_id: Mapped[Optional[int]] = mapped_column(
        BIGINT_ID, ForeignKey("xc_test_persona.id", ondelete="SET NULL")
    )
    scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    total_score: Mapped[Optional[int]] = mapped_column(Integer)
    duration: Mapped[Optional[int]] = mapped_column(Integer)


class TestAnswer(Base):
    __tablename__ = "xc_test_answer"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_test_record.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_question.id", ondelete="RESTRICT"), nullable=False
    )
    answer_value: Mapped[dict] = mapped_column(JSON, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
