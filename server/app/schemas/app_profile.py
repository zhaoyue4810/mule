from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProfileDimensionAggregate(BaseModel):
    dim_code: str
    total_score: float


class ProfilePersonaAggregate(BaseModel):
    persona_key: str | None = None
    persona_name: str | None = None
    count: int


class ProfileReportHistoryItem(BaseModel):
    record_id: int
    test_code: str
    test_name: str
    persona_key: str | None = None
    persona_name: str | None = None
    summary: str
    total_score: int | None = None
    duration_seconds: int | None = None
    completed_at: datetime


class AppProfileOverview(BaseModel):
    user_id: int
    nickname: str
    avatar_value: str
    test_count: int
    distinct_test_count: int
    avg_duration_seconds: int
    last_test_at: datetime | None = None
    dominant_dimensions: list[ProfileDimensionAggregate] = Field(default_factory=list)
    persona_distribution: list[ProfilePersonaAggregate] = Field(default_factory=list)
    recent_reports: list[ProfileReportHistoryItem] = Field(default_factory=list)
