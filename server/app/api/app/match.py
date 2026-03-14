from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.app_match import (
    MatchCreateRequest,
    MatchCreateResponse,
    MatchHistoryResponse,
    MatchInviteDetail,
    MatchJoinResponse,
    MatchResultPayload,
)
from app.services.match_service import MatchService

router = APIRouter(tags=["app-match"])


@router.post("/match/create", response_model=MatchCreateResponse)
async def create_match_invite(
    payload: MatchCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchCreateResponse:
    service = MatchService(db)
    try:
        data = await service.create_invite(user=user, test_code=payload.test_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MatchCreateResponse(**data)


@router.get("/match/invite/{code}", response_model=MatchInviteDetail)
async def get_match_invite_detail(
    code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchInviteDetail:
    service = MatchService(db)
    try:
        data = await service.get_invite_detail(code=code, user=user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MatchInviteDetail(**data)


@router.post("/match/join/{code}", response_model=MatchJoinResponse)
async def join_match_invite(
    code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchJoinResponse:
    service = MatchService(db)
    try:
        data = await service.join_invite(code=code, user=user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MatchJoinResponse(**data)


@router.get("/match/result/{session_id}", response_model=MatchResultPayload)
async def get_match_result(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchResultPayload:
    service = MatchService(db)
    try:
        data = await service.get_result(session_id=session_id, user=user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return MatchResultPayload(**data)


@router.get("/match/history", response_model=MatchHistoryResponse)
async def get_match_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchHistoryResponse:
    service = MatchService(db)
    data = await service.get_history(user=user)
    return MatchHistoryResponse(**data)
