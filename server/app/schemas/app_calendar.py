from __future__ import annotations

from pydantic import BaseModel, Field


class CalendarEventItem(BaseModel):
    source: str
    label: str
    mood_level: int | None = None
    emoji: str | None = None


class CalendarDayDetail(BaseModel):
    date: str
    activity_count: int
    intensity: int
    mood_level: int | None = None
    mood_emoji: str | None = None
    events: list[CalendarEventItem] = Field(default_factory=list)


class CalendarMonthPayload(BaseModel):
    year: int
    month: int
    items: list[CalendarDayDetail] = Field(default_factory=list)


class CalendarYearPayload(BaseModel):
    year: int
    items: list[CalendarDayDetail] = Field(default_factory=list)


class CalendarStatsPayload(BaseModel):
    current_streak: int
    active_days: int
    average_mood: float
    best_streak: int


class MoodRecordRequest(BaseModel):
    mood_level: int
    record_date: str | None = None
