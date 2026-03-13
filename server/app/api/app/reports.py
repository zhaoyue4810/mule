from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.app_report import AppReportDetail
from app.services.app_report_service import AppReportService

router = APIRouter(tags=["app-reports"])


@router.get("/reports/{record_id}", response_model=AppReportDetail)
async def get_report_detail(
    record_id: int,
    db: AsyncSession = Depends(get_db),
) -> AppReportDetail:
    service = AppReportService(db)
    try:
        detail = await service.get_report_detail(record_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AppReportDetail(**detail)
