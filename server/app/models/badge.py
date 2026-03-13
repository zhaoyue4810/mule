from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BIGINT_ID, Base, TimestampMixin


class BadgeDefinition(Base):
    __tablename__ = "xc_badge_definition"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    badge_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    unlock_rule: Mapped[dict] = mapped_column(JSON, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yaml_source: Mapped[str | None] = mapped_column(String(50))


class UserBadge(TimestampMixin, Base):
    __tablename__ = "xc_user_badge"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_ID, ForeignKey("xc_user.id", ondelete="CASCADE"), nullable=False
    )
    badge_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_badge_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    tier: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    unlock_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
