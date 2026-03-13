from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BIGINT_ID, Base, UpdateTimestampMixin


class User(UpdateTimestampMixin, Base):
    __tablename__ = "xc_user"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    openid: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    unionid: Mapped[Optional[str]] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    nickname: Mapped[str] = mapped_column(String(50), default="探索者", nullable=False)
    avatar_type: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    avatar_value: Mapped[str] = mapped_column(String(255), default="🧠", nullable=False)
    bio: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    gender: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    birth_year: Mapped[Optional[int]] = mapped_column(Integer)
    birth_month: Mapped[Optional[int]] = mapped_column(Integer)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    sound_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)

    settings: Mapped["UserSetting | None"] = relationship(back_populates="user")
    memory: Mapped["UserMemory | None"] = relationship(back_populates="user")


class UserSetting(Base):
    __tablename__ = "xc_user_setting"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    notif_match: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notif_result: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notif_friend: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notif_system: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    privacy_show_profile: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    privacy_show_history: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    privacy_allow_match: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    privacy_anonymous: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="settings")


class UserMemory(UpdateTimestampMixin, Base):
    __tablename__ = "xc_user_memory"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    test_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_duration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_score: Mapped[float] = mapped_column(default=0, nullable=False)
    fav_categories: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    know_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_test_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="memory")
