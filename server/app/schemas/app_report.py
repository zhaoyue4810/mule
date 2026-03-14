from __future__ import annotations

from pydantic import BaseModel, Field


class ReportDimensionHighlight(BaseModel):
    dim_code: str
    score: float


class ReportRadarDimension(BaseModel):
    dim_code: str
    label: str
    score: float
    normalized_score: float


class ReportPersonaTag(BaseModel):
    label: str
    tone: str


class ReportSoulWeather(BaseModel):
    title: str
    mood: str
    description: str


class ReportMetaphorCard(BaseModel):
    category: str
    title: str
    subtitle: str
    emoji: str


class ReportDNAItem(BaseModel):
    dim_code: str
    label: str
    percentage: int


class ReportActionGuide(BaseModel):
    title: str
    description: str


class ReportShareCard(BaseModel):
    theme: str
    background: str
    title: str
    subtitle: str
    accent: str
    badge: str
    footer: str
    stat_chips: list[str] = Field(default_factory=list)
    highlight_lines: list[str] = Field(default_factory=list)
    share_text: str


class ReportPersonaPayload(BaseModel):
    persona_key: str | None = None
    persona_name: str | None = None
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)


class AppReportDetail(BaseModel):
    report_id: int
    record_id: int
    test_code: str
    test_name: str
    version: int
    total_score: int | None = None
    summary: str
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    top_dimensions: list[ReportDimensionHighlight] = Field(default_factory=list)
    radar_dimensions: list[ReportRadarDimension] = Field(default_factory=list)
    persona_tags: list[ReportPersonaTag] = Field(default_factory=list)
    soul_weather: ReportSoulWeather
    metaphor_cards: list[ReportMetaphorCard] = Field(default_factory=list)
    dna_segments: list[ReportDNAItem] = Field(default_factory=list)
    action_guides: list[ReportActionGuide] = Field(default_factory=list)
    result_tier: str
    persona: ReportPersonaPayload
    answered_count: int
    duration_seconds: int | None = None
    ai_status: str
    ai_text: str | None = None
    share_card_url: str | None = None
    share_card: ReportShareCard
