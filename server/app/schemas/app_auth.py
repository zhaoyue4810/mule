from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuthUserPayload(BaseModel):
    user_id: int
    nickname: str
    avatar_value: str
    is_guest: bool
    has_openid: bool
    has_phone: bool
    masked_phone: str | None = None


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    user: AuthUserPayload


class GuestAuthRequest(BaseModel):
    nickname: str | None = None


class WechatMiniProgramLoginRequest(BaseModel):
    code: str
    nickname: str | None = None
    avatar_value: str | None = None


class PhoneSendCodeRequest(BaseModel):
    phone: str


class PhoneSendCodeResponse(BaseModel):
    phone: str
    expires_in_seconds: int
    provider: str
    debug_code: str | None = None


class PhoneLoginRequest(BaseModel):
    phone: str
    code: str


class PhoneBindRequest(BaseModel):
    phone: str
    code: str
