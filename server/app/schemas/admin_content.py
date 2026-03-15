from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdminTestSummary(BaseModel):
    test_code: str
    title: str
    category: str
    is_match_enabled: bool
    version_count: int


class AdminTestVersionSummary(BaseModel):
    id: int
    version: int
    status: str
    description: str | None = None
    duration_hint: str | None = None
    published_at: datetime | None = None
    created_at: datetime


class AdminTestDetail(BaseModel):
    test_code: str
    title: str
    category: str
    is_match_enabled: bool
    participant_count: int
    sort_order: int
    yaml_source: str | None = None
    published_version_id: int | None = None
    published_version: int | None = None


class AdminTestVersionDetail(BaseModel):
    id: int
    test_code: str
    title: str
    category: str
    version: int
    status: str
    description: str | None = None
    duration_hint: str | None = None
    cover_gradient: str | None = None
    report_template_code: str | None = None
    published_at: datetime | None = None
    created_at: datetime
    question_count: int
    dimension_count: int
    persona_count: int
    is_published: bool


class AdminDimensionPayload(BaseModel):
    dim_code: str
    dim_name: str
    max_score: int = 100
    sort_order: int


class AdminOptionPayload(BaseModel):
    option_code: str | None = None
    seq: int
    label: str
    emoji: str | None = None
    value: float
    score_rules: dict | None = None
    ext_config: dict | None = None


class AdminQuestionPayload(BaseModel):
    question_code: str | None = None
    seq: int
    question_text: str
    interaction_type: str
    emoji: str | None = None
    config: dict | None = None
    dim_weights: dict = Field(default_factory=dict)
    options: list[AdminOptionPayload] = Field(default_factory=list)


class AdminPersonaPayload(BaseModel):
    persona_key: str
    persona_name: str
    emoji: str | None = None
    rarity_percent: int | None = None
    description: str | None = None
    soul_signature: str | None = None
    keywords: list[str] = Field(default_factory=list)
    dim_pattern: dict = Field(default_factory=dict)
    capsule_prompt: str | None = None


class AdminTestVersionContent(BaseModel):
    id: int
    test_code: str
    title: str
    category: str
    is_match_enabled: bool
    participant_count: int
    sort_order: int
    version: int
    status: str
    description: str | None = None
    duration_hint: str | None = None
    cover_gradient: str | None = None
    report_template_code: str | None = None
    dimensions: list[AdminDimensionPayload] = Field(default_factory=list)
    questions: list[AdminQuestionPayload] = Field(default_factory=list)
    personas: list[AdminPersonaPayload] = Field(default_factory=list)


class AdminTestVersionContentUpdateRequest(BaseModel):
    title: str
    category: str
    is_match_enabled: bool = False
    participant_count: int = 0
    sort_order: int = 0
    description: str | None = None
    duration_hint: str | None = None
    cover_gradient: str | None = None
    report_template_code: str | None = None
    dimensions: list[AdminDimensionPayload] = Field(default_factory=list)
    questions: list[AdminQuestionPayload] = Field(default_factory=list)
    personas: list[AdminPersonaPayload] = Field(default_factory=list)


class AdminCreateVersionRequest(BaseModel):
    source_version_id: int | None = None
    source_version: int | None = None
    clone_content: bool = True
    description: str | None = None


class PublishVersionRequest(BaseModel):
    version_id: int | None = None
    version: int | None = None
    note: str | None = None
