from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MatchCreateRequest(BaseModel):
    test_code: str


class MatchUserSummary(BaseModel):
    user_id: int
    nickname: str
    avatar_value: str


class MatchBadgeSummary(BaseModel):
    badge_key: str
    name: str
    emoji: str
    unlocked_at: datetime


class MatchDimensionComparisonItem(BaseModel):
    dim_code: str
    initiator_score: float
    partner_score: float
    difference: float
    similarity: int
    relation: str


class MatchSessionSummary(BaseModel):
    session_id: int
    test_code: str
    test_name: str
    status: str
    invite_code: str
    invite_link: str | None = None
    compatibility_score: int | None = None
    created_at: datetime
    completed_at: datetime | None = None


class MatchCreateResponse(MatchSessionSummary):
    initiator: MatchUserSummary
    share_message: str


class MatchInviteDetail(MatchSessionSummary):
    initiator: MatchUserSummary
    partner: MatchUserSummary | None = None
    partner_joined: bool
    requires_test_completion: bool = False
    can_join: bool = False


class MatchJoinResponse(BaseModel):
    session_id: int
    status: str
    result_ready: bool
    compatibility_score: int | None = None
    unlocked_badges: list[MatchBadgeSummary] = Field(default_factory=list)


class MatchResultPayload(BaseModel):
    session_id: int
    status: str
    test_code: str
    test_name: str
    compatibility_score: int
    tier: str
    analysis: str
    created_at: datetime
    completed_at: datetime | None = None
    initiator: MatchUserSummary
    partner: MatchUserSummary
    dimension_comparison: list[MatchDimensionComparisonItem] = Field(default_factory=list)
    similar_dimensions: list[str] = Field(default_factory=list)
    complementary_dimensions: list[str] = Field(default_factory=list)
    unlocked_badges: list[MatchBadgeSummary] = Field(default_factory=list)


class MatchHistoryItem(BaseModel):
    session_id: int
    test_code: str
    test_name: str
    status: str
    partner: MatchUserSummary | None = None
    compatibility_score: int | None = None
    tier: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class MatchHistoryResponse(BaseModel):
    items: list[MatchHistoryItem] = Field(default_factory=list)
    duo_badges: list[MatchBadgeSummary] = Field(default_factory=list)
