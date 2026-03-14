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


class AdminAiTaskMetrics(BaseModel):
    total: int
    completed: int
    failed: int
    running: int
    pending: int
    success_rate: float
    failure_rate: float
    fallback_rate: float
    avg_duration_ms: int
    p95_duration_ms: int
    tasks_last_24h: int
    failures_last_24h: int
    series: list[dict] = []


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


class AdminAiPromptTemplateHistoryItem(AdminAiPromptTemplateSummary):
    template_id: int


class AdminAiPromptTemplateComparePayload(BaseModel):
    template_id: int
    from_version: int
    to_version: int
    system_prompt_before: str
    system_prompt_after: str
    user_prompt_before: str
    user_prompt_after: str


class AdminAiRetryResponse(BaseModel):
    retried: int
    task_ids: list[int]


class AdminAiPromptTemplateUpdateRequest(BaseModel):
    system_prompt: str
    user_prompt_tpl: str
    model_tier: str
    temperature: float
    max_tokens: int
    is_active: bool = True
    bump_version: bool = True
