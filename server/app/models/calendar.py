from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, JSON, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BIGINT_ID, Base, TimestampMixin


class CalendarEntry(Base):
    __tablename__ = "xc_calendar_entry"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    mood_level: Mapped[int | None] = mapped_column(SmallInteger)
    test_record_id: Mapped[int | None] = mapped_column(
        BIGINT_ID, ForeignKey("xc_test_record.id", ondelete="SET NULL")
    )
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)


class DailySoulQuestion(Base):
    __tablename__ = "xc_daily_soul_question"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    question_text: Mapped[str] = mapped_column(String(300), nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)
    insights: Mapped[dict] = mapped_column(JSON, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yaml_source: Mapped[str | None] = mapped_column(String(50))


class DailySoulAnswer(Base):
    __tablename__ = "xc_daily_soul_answer"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_daily_soul_question.id", ondelete="CASCADE"),
        nullable=False,
    )
    answer_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    answer_date: Mapped[date] = mapped_column(Date, nullable=False)
