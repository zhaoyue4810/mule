from __future__ import annotations

from pydantic import BaseModel


class ReportAiStatusPayload(BaseModel):
    record_id: int
    status: str
    provider: str | None = None
    model_used: str | None = None
    content: str | None = None
    updated: bool = False


class ReportAiRetryRequest(BaseModel):
    record_id: int
