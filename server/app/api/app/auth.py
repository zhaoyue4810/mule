from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.app_auth import (
    AuthSessionResponse,
    AuthUserPayload,
    GuestAuthRequest,
    PhoneBindRequest,
    PhoneLoginRequest,
    PhoneSendCodeRequest,
    PhoneSendCodeResponse,
    WechatMiniProgramLoginRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(tags=["app-auth"])


@router.post("/auth/guest", response_model=AuthSessionResponse)
async def guest_login(
    payload: GuestAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthSessionResponse:
    service = AuthService(db)
    session = await service.create_guest_session(payload.nickname)
    return AuthSessionResponse(**session)


@router.get("/auth/me", response_model=AuthUserPayload)
async def get_auth_me(
    user: User = Depends(get_current_user),
) -> AuthUserPayload:
    return AuthUserPayload(
        user_id=user.id,
        nickname=user.nickname,
        avatar_value=user.avatar_value,
        is_guest=not bool(user.openid or user.phone),
        has_openid=bool(user.openid),
        has_phone=bool(user.phone),
        masked_phone=(
            f"{user.phone[:3]}****{user.phone[-4:]}"
            if user.phone and len(user.phone) >= 7
            else user.phone
        ),
    )


@router.post("/auth/wechat/mini-program", response_model=AuthSessionResponse)
async def wechat_mini_program_login(
    payload: WechatMiniProgramLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthSessionResponse:
    service = AuthService(db)
    try:
        session = await service.login_with_wechat_mini_program(
            code=payload.code,
            nickname=payload.nickname,
            avatar_value=payload.avatar_value,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AuthSessionResponse(**session)


@router.post("/auth/wx-login", response_model=AuthSessionResponse)
async def wechat_mini_program_login_alias(
    payload: WechatMiniProgramLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthSessionResponse:
    return await wechat_mini_program_login(payload, db)


@router.post("/auth/phone/send-code", response_model=PhoneSendCodeResponse)
async def send_phone_code(
    payload: PhoneSendCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> PhoneSendCodeResponse:
    service = AuthService(db)
    try:
        result = await service.send_phone_code(payload.phone)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return PhoneSendCodeResponse(**result)


@router.post("/auth/phone-login", response_model=AuthSessionResponse)
async def phone_login(
    payload: PhoneLoginRequest,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> AuthSessionResponse:
    service = AuthService(db)
    try:
        session = await service.login_with_phone(
            phone=payload.phone,
            code=payload.code,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AuthSessionResponse(**session)


@router.post("/auth/phone/bind", response_model=AuthSessionResponse)
async def bind_phone(
    payload: PhoneBindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthSessionResponse:
    service = AuthService(db)
    try:
        session = await service.login_with_phone(
            phone=payload.phone,
            code=payload.code,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AuthSessionResponse(**session)
