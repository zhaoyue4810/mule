from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.admin_ai import (
    AdminAiRetryResponse,
    AdminAiTaskMetrics,
    AdminAiTaskDetail,
    AdminAiTaskOverview,
    AdminAiPromptTemplateComparePayload,
    AdminAiPromptTemplateHistoryItem,
    AdminAiPromptTemplateSummary,
    AdminAiPromptTemplateUpdateRequest,
    AdminAiTaskPage,
)
from app.services.admin_ai_service import AdminAiService

router = APIRouter(tags=["admin-ai"])


@router.get("/task/page", response_model=AdminAiTaskPage)
async def list_ai_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    task_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> AdminAiTaskPage:
    service = AdminAiService(db)
    payload = await service.list_tasks(
        page=page,
        page_size=page_size,
        task_type=task_type,
        status=status,
        provider=provider,
        date_from=date_from,
        date_to=date_to,
    )
    return AdminAiTaskPage(**payload)


@router.get("/task/overview", response_model=AdminAiTaskOverview)
async def get_ai_task_overview(
    db: AsyncSession = Depends(get_db),
) -> AdminAiTaskOverview:
    service = AdminAiService(db)
    return AdminAiTaskOverview(**(await service.get_task_overview()))


@router.get("/task/metrics", response_model=AdminAiTaskMetrics)
async def get_ai_task_metrics(
    bucket: str = Query(default="day", pattern="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
) -> AdminAiTaskMetrics:
    service = AdminAiService(db)
    return AdminAiTaskMetrics(**(await service.get_task_metrics_by_bucket(bucket=bucket)))


@router.get("/task/{task_id}", response_model=AdminAiTaskDetail)
async def get_ai_task_detail(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> AdminAiTaskDetail:
    service = AdminAiService(db)
    try:
        item = await service.get_task_detail(task_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminAiTaskDetail(**item)


@router.get("/prompt/list", response_model=list[AdminAiPromptTemplateSummary])
async def list_prompt_templates(
    db: AsyncSession = Depends(get_db),
) -> list[AdminAiPromptTemplateSummary]:
    service = AdminAiService(db)
    return [
        AdminAiPromptTemplateSummary(**item)
        for item in await service.list_prompt_templates()
    ]


@router.put("/prompt/{template_id}", response_model=AdminAiPromptTemplateSummary)
async def update_prompt_template(
    template_id: int,
    payload: AdminAiPromptTemplateUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminAiPromptTemplateSummary:
    service = AdminAiService(db)
    try:
        item = await service.update_prompt_template(template_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminAiPromptTemplateSummary(**item)


@router.get("/prompt/{template_id}/history", response_model=list[AdminAiPromptTemplateHistoryItem])
async def list_prompt_template_history(
    template_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[AdminAiPromptTemplateHistoryItem]:
    service = AdminAiService(db)
    try:
        items = await service.list_prompt_template_history(template_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [AdminAiPromptTemplateHistoryItem(**item) for item in items]


@router.get("/prompt/{template_id}/compare", response_model=AdminAiPromptTemplateComparePayload)
async def compare_prompt_template(
    template_id: int,
    from_version: int | None = Query(default=None, ge=1),
    to_version: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> AdminAiPromptTemplateComparePayload:
    service = AdminAiService(db)
    try:
        payload = await service.compare_prompt_template_versions(
            template_id,
            from_version=from_version,
            to_version=to_version,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminAiPromptTemplateComparePayload(**payload)


@router.post("/task/{task_id}/retry", response_model=AdminAiRetryResponse)
async def retry_ai_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> AdminAiRetryResponse:
    service = AdminAiService(db)
    try:
        payload = await service.retry_task(task_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AdminAiRetryResponse(**payload)


@router.post("/task/retry-failed", response_model=AdminAiRetryResponse)
async def retry_failed_ai_tasks(
    db: AsyncSession = Depends(get_db),
) -> AdminAiRetryResponse:
    payload = await AdminAiService(db).retry_failed_tasks()
    return AdminAiRetryResponse(**payload)
