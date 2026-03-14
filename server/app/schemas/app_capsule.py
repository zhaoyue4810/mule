from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class TimeCapsuleCreateRequest(BaseModel):
    message: str
    duration_days: int
    report_id: int


class TimeCapsuleItem(BaseModel):
    id: int
    message: str
    persona_title: str | None = None
    persona_icon: str | None = None
    test_id: int | None = None
    report_id: int | None = None
    created_at: datetime
    unlock_date: date
    duration_days: int
    is_read: bool
    is_unlocked: bool
    days_remaining: int = 0


class TimeCapsuleCreateResponse(TimeCapsuleItem):
    pass


class TimeCapsuleListResponse(BaseModel):
    items: list[TimeCapsuleItem] = Field(default_factory=list)


class TimeCapsuleRevealResponse(BaseModel):
    item: TimeCapsuleItem
    revealed: bool


class TimeCapsuleCheckResponse(BaseModel):
    has_revealable: bool
    items: list[TimeCapsuleItem] = Field(default_factory=list)
