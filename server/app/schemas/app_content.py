from __future__ import annotations

from pydantic import BaseModel, Field


class PublishedTestSummary(BaseModel):
    test_code: str
    name: str
    category: str
    is_match_enabled: bool
    participant_count: int
    version: int
    question_count: int
    duration_hint: str | None = None
    cover_gradient: str | None = None


class PublishedDimensionSummary(BaseModel):
    dim_code: str
    dim_name: str
    max_score: int
    sort_order: int


class PublishedPersonaSummary(BaseModel):
    persona_key: str
    persona_name: str
    emoji: str | None = None
    rarity_percent: int | None = None
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)


class PublishedOptionPayload(BaseModel):
    option_code: str | None = None
    seq: int
    label: str
    emoji: str | None = None
    value: float


class PublishedQuestionPayload(BaseModel):
    question_code: str | None = None
    seq: int
    question_text: str
    interaction_type: str
    emoji: str | None = None
    config: dict | None = None
    dim_weights: dict = Field(default_factory=dict)
    options: list[PublishedOptionPayload] = Field(default_factory=list)


class PublishedTestDetail(BaseModel):
    test_code: str
    name: str
    category: str
    is_match_enabled: bool
    participant_count: int
    sort_order: int
    version: int
    question_count: int
    dimension_count: int
    persona_count: int
    duration_hint: str | None = None
    description: str | None = None
    cover_gradient: str | None = None
    report_template_code: str | None = None
    dimensions: list[PublishedDimensionSummary] = Field(default_factory=list)
    personas: list[PublishedPersonaSummary] = Field(default_factory=list)


class PublishedTestQuestionnaire(BaseModel):
    test_code: str
    name: str
    category: str
    version: int
    duration_hint: str | None = None
    question_count: int
    questions: list[PublishedQuestionPayload] = Field(default_factory=list)


class TestSubmitAnswerPayload(BaseModel):
    question_seq: int = Field(ge=1)
    option_code: str | None = None
    numeric_value: float | None = None
    ordered_option_codes: list[str] | None = None
    point: dict[str, float] | None = None


class TestSubmitRequest(BaseModel):
    user_id: int | None = None
    nickname: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    answers: list[TestSubmitAnswerPayload] = Field(default_factory=list)


class SubmittedAnswerSummary(BaseModel):
    question_seq: int
    option_code: str | None = None
    label: str


class UnlockedBadgeSummary(BaseModel):
    badge_key: str
    name: str
    emoji: str
    tier: int = 1


class UnlockedSoulFragmentSummary(BaseModel):
    fragment_key: str
    name: str
    emoji: str | None = None
    category: str
    insight: str | None = None


class TestSubmitResponse(BaseModel):
    record_id: int
    user_id: int
    test_code: str
    version: int
    total_score: int
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    persona_key: str | None = None
    persona_name: str | None = None
    report_summary: str
    answers: list[SubmittedAnswerSummary] = Field(default_factory=list)
    unlocked_badges: list[UnlockedBadgeSummary] = Field(default_factory=list)
    unlocked_fragments: list[UnlockedSoulFragmentSummary] = Field(default_factory=list)
