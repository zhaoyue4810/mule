from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BIGINT_ID, Base, TimestampMixin


class TimeCapsule(TimestampMixin, Base):
    __tablename__ = "xc_time_capsule"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    persona_title: Mapped[str | None] = mapped_column(String(100))
    persona_icon: Mapped[str | None] = mapped_column(String(10))
    test_id: Mapped[int | None] = mapped_column(
        BIGINT_ID, ForeignKey("xc_test.id", ondelete="SET NULL")
    )
    report_id: Mapped[int | None] = mapped_column(
        BIGINT_ID, ForeignKey("xc_report_snapshot.id", ondelete="SET NULL")
    )
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    unlock_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SoulFragmentDefinition(Base):
    __tablename__ = "xc_soul_fragment_definition"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    fragment_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    emoji: Mapped[str | None] = mapped_column(String(10))
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    required_test_code: Mapped[str | None] = mapped_column(String(50))
    insight: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yaml_source: Mapped[str | None] = mapped_column(String(50))


class UserSoulFragment(TimestampMixin, Base):
    __tablename__ = "xc_user_soul_fragment"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False
    )
    fragment_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_soul_fragment_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
