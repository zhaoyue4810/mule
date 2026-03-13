from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BIGINT_ID, Base, TimestampMixin


class Test(TimestampMixin, Base):
    __tablename__ = "xc_test"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    test_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    emoji: Mapped[Optional[str]] = mapped_column(String(10))
    is_match_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    participant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yaml_source: Mapped[Optional[str]] = mapped_column(String(100))

    versions: Mapped[list["TestVersion"]] = relationship(back_populates="test")


class TestVersion(TimestampMixin, Base):
    __tablename__ = "xc_test_version"
    __table_args__ = (UniqueConstraint("test_id", "version"),)

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_test.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    duration_hint: Mapped[Optional[str]] = mapped_column(String(20))
    cover_gradient: Mapped[Optional[str]] = mapped_column(String(200))
    report_template_code: Mapped[Optional[str]] = mapped_column(String(50))
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    test: Mapped[Test] = relationship(back_populates="versions")
    dimensions: Mapped[list["Dimension"]] = relationship(back_populates="version")
    questions: Mapped[list["Question"]] = relationship(back_populates="version")
    personas: Mapped[list["TestPersona"]] = relationship(back_populates="version")


class Dimension(Base):
    __tablename__ = "xc_dimension"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    version_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_test_version.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dim_code: Mapped[str] = mapped_column(String(50), nullable=False)
    dim_name: Mapped[str] = mapped_column(String(50), nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    version: Mapped[TestVersion] = relationship(back_populates="dimensions")


class Question(Base):
    __tablename__ = "xc_question"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    version_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_test_version.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_code: Mapped[Optional[str]] = mapped_column(String(50))
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(String(500), nullable=False)
    interaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    emoji: Mapped[Optional[str]] = mapped_column(String(10))
    config: Mapped[dict | None] = mapped_column(JSON)
    dim_weights: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    version: Mapped[TestVersion] = relationship(back_populates="questions")
    options: Mapped[list["Option"]] = relationship(back_populates="question")


class Option(Base):
    __tablename__ = "xc_option"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_question.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    option_code: Mapped[Optional[str]] = mapped_column(String(20))
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    emoji: Mapped[Optional[str]] = mapped_column(String(10))
    value: Mapped[float] = mapped_column(nullable=False)
    score_rules: Mapped[dict | None] = mapped_column(JSON)
    ext_config: Mapped[dict | None] = mapped_column(JSON)

    question: Mapped[Question] = relationship(back_populates="options")


class TestPersona(Base):
    __tablename__ = "xc_test_persona"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True, autoincrement=True)
    version_id: Mapped[int] = mapped_column(
        BIGINT_ID,
        ForeignKey("xc_test_version.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    persona_key: Mapped[str] = mapped_column(String(50), nullable=False)
    persona_name: Mapped[str] = mapped_column(String(100), nullable=False)
    emoji: Mapped[Optional[str]] = mapped_column(String(10))
    rarity_percent: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)
    soul_signature: Mapped[Optional[str]] = mapped_column(String(200))
    keywords: Mapped[list[str] | None] = mapped_column(JSON)
    dim_pattern: Mapped[dict] = mapped_column(JSON, nullable=False)
    capsule_prompt: Mapped[Optional[str]] = mapped_column(String(300))

    version: Mapped[TestVersion] = relationship(back_populates="personas")
