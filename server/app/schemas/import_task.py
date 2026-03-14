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


class ImportTaskRejectRequest(BaseModel):
    reason: str | None = None


class ImportPreviewPayload(BaseModel):
    file_type: str
    title: str
    summary: dict[str, Any]


class ImportTaskResponse(BaseModel):
    id: int
    file_type: str
    file_url: str
    file_name: str
    status: str
    parse_log: str | None = None
    ai_log: str | None = None
    preview_json: dict[str, Any] | None = None
    operator_id: int | None = None
    operator_name: str | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, task: Any) -> "ImportTaskResponse":
        return cls(
            id=task.id,
            file_type=task.file_type,
            file_url=task.file_url,
            file_name=str(task.file_url).split("/")[-1],
            status=task.status,
            parse_log=task.parse_log,
            ai_log=task.ai_log,
            preview_json=task.preview_json,
            operator_id=task.operator_id,
            operator_name=str(task.operator_id) if task.operator_id is not None else "admin",
            created_at=task.created_at,
        )


class ImportTaskPageResponse(BaseModel):
    items: list[ImportTaskResponse]
    total: int
    page: int
    size: int
