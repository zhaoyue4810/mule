from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.schemas.app_ai import ReportAiRetryRequest, ReportAiStatusPayload
from app.services.report_ai_service import ReportAiService

router = APIRouter(tags=["app-ai"])


@router.get("/reports/{record_id}/ai-status", response_model=ReportAiStatusPayload)
async def get_report_ai_status(
    record_id: int,
    db: AsyncSession = Depends(get_db),
) -> ReportAiStatusPayload:
    service = ReportAiService(db)
    try:
        payload = await service.get_report_ai_status(record_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReportAiStatusPayload(**payload)


@router.post("/ai/report/retry", response_model=ReportAiStatusPayload)
async def retry_report_ai_generation(
    payload: ReportAiRetryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ReportAiStatusPayload:
    service = ReportAiService(db)
    try:
        await service.enqueue_report_analysis(payload.record_id)
        background_tasks.add_task(
            ReportAiService.run_report_analysis_job,
            async_sessionmaker(db.bind, expire_on_commit=False),
            payload.record_id,
        )
        status_payload = await service.get_report_ai_status(payload.record_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReportAiStatusPayload(**status_payload)
