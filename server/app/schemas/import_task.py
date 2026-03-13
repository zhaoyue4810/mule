from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ImportTaskCreateRequest(BaseModel):
    file_type: str = Field(pattern="^(html|docx)$")
    file_path: str
    operator_id: int | None = None


class ImportTaskParseRequest(BaseModel):
    force: bool = False


class ImportTaskApplyRequest(BaseModel):
    note: str | None = None


class ImportPreviewPayload(BaseModel):
    file_type: str
    title: str
    summary: dict[str, Any]


class ImportTaskResponse(BaseModel):
    id: int
    file_type: str
    file_url: str
    status: str
    parse_log: str | None = None
    ai_log: str | None = None
    preview_json: dict[str, Any] | None = None
    operator_id: int | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, task: Any) -> "ImportTaskResponse":
        return cls(
            id=task.id,
            file_type=task.file_type,
            file_url=task.file_url,
            status=task.status,
            parse_log=task.parse_log,
            ai_log=task.ai_log,
            preview_json=task.preview_json,
            operator_id=task.operator_id,
            created_at=task.created_at,
        )
