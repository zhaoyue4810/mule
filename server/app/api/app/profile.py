from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.app_profile import (
    AppProfileOverview,
    DailyQuestionAnswerRequest,
    DailyQuestionStatePayload,
    ProfileReportHistoryItem,
)
from app.services.app_profile_service import AppProfileService
from app.services.daily_question_service import DailyQuestionService

router = APIRouter(tags=["app-profile"])


@router.get("/profile/me/overview", response_model=AppProfileOverview)
async def get_my_profile_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppProfileOverview:
    service = AppProfileService(db)
    overview = await service.get_overview(user.id)
    return AppProfileOverview(**overview)


@router.get("/profile/me/reports", response_model=list[ProfileReportHistoryItem])
async def list_my_profile_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProfileReportHistoryItem]:
    service = AppProfileService(db)
    reports = await service.list_reports(user.id)
    return [ProfileReportHistoryItem(**item) for item in reports]


@router.get("/profile/me/daily-question", response_model=DailyQuestionStatePayload)
async def get_my_daily_question(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DailyQuestionStatePayload:
    service = DailyQuestionService(db)
    state = await service.get_today_question(user_id=user.id)
    return DailyQuestionStatePayload(**state.__dict__)


@router.post("/profile/me/daily-question", response_model=DailyQuestionStatePayload)
async def submit_my_daily_question(
    payload: DailyQuestionAnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DailyQuestionStatePayload:
    service = DailyQuestionService(db)
    try:
        state = await service.submit_answer(
            user_id=user.id,
            question_id=payload.question_id,
            answer_index=payload.answer_index,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DailyQuestionStatePayload(**state.__dict__)


@router.get("/profile/{user_id}/overview", response_model=AppProfileOverview)
async def get_profile_overview(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> AppProfileOverview:
    service = AppProfileService(db)
    try:
        overview = await service.get_overview(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AppProfileOverview(**overview)


@router.get("/profile/{user_id}/reports", response_model=list[ProfileReportHistoryItem])
async def list_profile_reports(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ProfileReportHistoryItem]:
    service = AppProfileService(db)
    try:
        reports = await service.list_reports(user_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [ProfileReportHistoryItem(**item) for item in reports]
