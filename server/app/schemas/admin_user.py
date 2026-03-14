from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdminUserSummary(BaseModel):
    id: int
    nickname: str
    avatar_value: str
    gender: int
    created_at: datetime
    test_count: int = 0
    status: str


class AdminUserListResponse(BaseModel):
    items: list[AdminUserSummary]
    total: int
    page: int
    size: int


class AdminUserTestRecord(BaseModel):
    record_id: int
    test_name: str
    total_score: int | None = None
    completed_at: datetime


class AdminUserMatchRecord(BaseModel):
    session_id: int
    test_name: str
    status: str
    compatibility_score: int | None = None
    created_at: datetime
    completed_at: datetime | None = None


class AdminUserBadge(BaseModel):
    badge_key: str
    name: str
    emoji: str
    tier: int
    unlock_count: int
    unlocked_at: datetime


class AdminUserDetail(BaseModel):
    id: int
    nickname: str
    avatar_value: str
    gender: int
    created_at: datetime
    status: str
    test_count: int
    match_count: int
    badges: list[AdminUserBadge]
    test_records: list[AdminUserTestRecord]
    match_records: list[AdminUserMatchRecord]


class AdminUserStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(ENABLED|DISABLED)$")
