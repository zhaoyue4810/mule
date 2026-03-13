from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth import get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.app_content import (
    PublishedTestDetail,
    PublishedTestQuestionnaire,
    PublishedTestSummary,
    TestSubmitRequest,
    TestSubmitResponse,
)
from app.services.app_content_service import AppContentService
from app.services.report_ai_service import ReportAiService
from app.services.test_submission_service import TestSubmissionService

router = APIRouter(tags=["app-tests"])


@router.get("/tests", response_model=list[PublishedTestSummary])
async def list_published_tests(
    db: AsyncSession = Depends(get_db),
) -> list[PublishedTestSummary]:
    service = AppContentService(db)
    return [
        PublishedTestSummary(**item) for item in await service.list_published_tests()
    ]


@router.get("/tests/{test_code}", response_model=PublishedTestDetail)
async def get_published_test_detail(
    test_code: str,
    db: AsyncSession = Depends(get_db),
) -> PublishedTestDetail:
    service = AppContentService(db)
    try:
        detail = await service.get_published_test_detail(test_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PublishedTestDetail(**detail)


@router.get("/tests/{test_code}/questionnaire", response_model=PublishedTestQuestionnaire)
async def get_published_test_questionnaire(
    test_code: str,
    db: AsyncSession = Depends(get_db),
) -> PublishedTestQuestionnaire:
    service = AppContentService(db)
    try:
        detail = await service.get_published_test_questionnaire(test_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PublishedTestQuestionnaire(**detail)


@router.post("/tests/{test_code}/submit", response_model=TestSubmitResponse)
async def submit_test_answers(
    test_code: str,
    payload: TestSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> TestSubmitResponse:
    if current_user is not None and payload.user_id is None:
        payload = payload.model_copy(update={"user_id": current_user.id})
    service = TestSubmissionService(db)
    try:
        result = await service.submit(test_code, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    ai_service = ReportAiService(db)
    await ai_service.enqueue_report_analysis(result["record_id"])
    background_tasks.add_task(
        ReportAiService.run_report_analysis_job,
        async_sessionmaker(db.bind, expire_on_commit=False),
        result["record_id"],
    )
    return TestSubmitResponse(**result)
