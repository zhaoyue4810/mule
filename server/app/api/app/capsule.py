from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.app_capsule import (
    TimeCapsuleCheckResponse,
    TimeCapsuleCreateRequest,
    TimeCapsuleCreateResponse,
    TimeCapsuleListResponse,
    TimeCapsuleRevealResponse,
)
from app.services.time_capsule_service import TimeCapsuleService

router = APIRouter(tags=["app-capsule"])


@router.post("/capsule/create", response_model=TimeCapsuleCreateResponse)
async def create_time_capsule(
    payload: TimeCapsuleCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TimeCapsuleCreateResponse:
    service = TimeCapsuleService(db)
    try:
        item = await service.create_capsule(
            user=user,
            message=payload.message,
            duration_days=payload.duration_days,
            report_id=payload.report_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TimeCapsuleCreateResponse(**item)


@router.get("/capsule/list", response_model=TimeCapsuleListResponse)
async def list_time_capsules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TimeCapsuleListResponse:
    items = await TimeCapsuleService(db).list_capsules(user=user)
    return TimeCapsuleListResponse(items=items)


@router.post("/capsule/{capsule_id}/reveal", response_model=TimeCapsuleRevealResponse)
async def reveal_time_capsule(
    capsule_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TimeCapsuleRevealResponse:
    service = TimeCapsuleService(db)
    try:
        item = await service.reveal_capsule(user=user, capsule_id=capsule_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TimeCapsuleRevealResponse(item=item, revealed=True)


@router.get("/capsule/check", response_model=TimeCapsuleCheckResponse)
async def check_time_capsule(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TimeCapsuleCheckResponse:
    payload = await TimeCapsuleService(db).check_revealable(user=user)
    return TimeCapsuleCheckResponse(**payload)
