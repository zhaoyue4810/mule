from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.admin_ai import (
    AdminAiTaskDetail,
    AdminAiTaskOverview,
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
    db: AsyncSession = Depends(get_db),
) -> AdminAiTaskPage:
    service = AdminAiService(db)
    payload = await service.list_tasks(
        page=page,
        page_size=page_size,
        task_type=task_type,
        status=status,
    )
    return AdminAiTaskPage(**payload)


@router.get("/task/overview", response_model=AdminAiTaskOverview)
async def get_ai_task_overview(
    db: AsyncSession = Depends(get_db),
) -> AdminAiTaskOverview:
    service = AdminAiService(db)
    return AdminAiTaskOverview(**(await service.get_task_overview()))


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
