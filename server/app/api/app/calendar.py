from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.app_calendar import (
    CalendarMonthPayload,
    CalendarStatsPayload,
    CalendarYearPayload,
    MoodRecordRequest,
)
from app.services.calendar_activity_service import CalendarActivityService

router = APIRouter(tags=["app-calendar"])


@router.get("/calendar/month", response_model=CalendarMonthPayload)
async def get_calendar_month(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarMonthPayload:
    service = CalendarActivityService(db)
    try:
        start = date(year, month, 1)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    next_month = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
    days = (next_month - start).days
    items = await service.build_heatmap(user_id=user.id, days=days, end_date=date(year, month, days))
    return CalendarMonthPayload(year=year, month=month, items=[item.__dict__ for item in items])


@router.get("/calendar/year", response_model=CalendarYearPayload)
async def get_calendar_year(
    year: int = Query(..., ge=2000, le=2100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarYearPayload:
    service = CalendarActivityService(db)
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    days = (end - start).days + 1
    items = await service.build_heatmap(user_id=user.id, days=days, end_date=end)
    return CalendarYearPayload(year=year, items=[item.__dict__ for item in items])


@router.get("/calendar/stats", response_model=CalendarStatsPayload)
async def get_calendar_stats(
    year: int | None = Query(default=None, ge=2000, le=2100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarStatsPayload:
    payload = await CalendarActivityService(db).build_stats(user_id=user.id, year=year)
    return CalendarStatsPayload(**payload)


@router.post("/calendar/mood", response_model=CalendarStatsPayload)
async def record_calendar_mood(
    payload: MoodRecordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarStatsPayload:
    if payload.mood_level < 1 or payload.mood_level > 5:
        raise HTTPException(status_code=422, detail="Mood level must be between 1 and 5")
    record_date = date.fromisoformat(payload.record_date) if payload.record_date else datetime.now().date()
    service = CalendarActivityService(db)
    await service.record_manual_mood(
        user_id=user.id,
        mood_level=payload.mood_level,
        record_date=record_date,
    )
    await db.commit()
    return CalendarStatsPayload(**(await service.build_stats(user_id=user.id)))
