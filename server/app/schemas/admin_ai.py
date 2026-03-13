from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AdminAiTaskSummary(BaseModel):
    id: int
    type: str
    ref_id: int
    status: str
    provider: str | None = None
    model_used: str | None = None
    prompt_version: str | None = None
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    error_message: str | None = None
    content_preview: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None


class AdminAiTaskPage(BaseModel):
    items: list[AdminAiTaskSummary]
    total: int
    page: int
    page_size: int


class AdminAiTaskDetail(AdminAiTaskSummary):
    provider_errors: list[str] = []
    content: str


class AdminAiTaskOverview(BaseModel):
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    fallback_runs: int
    failed_runs: int
    providers: dict[str, int]


class AdminAiPromptTemplateSummary(BaseModel):
    id: int
    template_code: str
    scene: str
    system_prompt: str
    user_prompt_tpl: str
    model_tier: str
    temperature: float
    max_tokens: int
    version: int
    is_active: bool
    created_at: datetime


class AdminAiPromptTemplateUpdateRequest(BaseModel):
    system_prompt: str
    user_prompt_tpl: str
    model_tier: str
    temperature: float
    max_tokens: int
    is_active: bool = True
    bump_version: bool = True
