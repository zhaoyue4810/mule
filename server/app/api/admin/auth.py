from __future__ import annotations

import bcrypt
from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.security import create_admin_token
from app.schemas.admin_auth import AdminLoginRequest, AdminLoginResponse

router = APIRouter(tags=["admin-auth"])


def _verify_password(plain_password: str, password_hash: str) -> bool:
    # bcrypt library prefers "$2b$". Existing hashes may use "$2y$".
    candidate = password_hash.encode("utf-8")
    if candidate.startswith(b"$2y$"):
        candidate = b"$2b$" + candidate[4:]
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), candidate)
    except ValueError:
        return False


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest) -> AdminLoginResponse:
    settings = get_settings()
    if payload.username != settings.admin_username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not _verify_password(payload.password, settings.admin_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, expires_at = create_admin_token(username=settings.admin_username)
    return AdminLoginResponse(
        access_token=token,
        expires_at=expires_at,
        username=settings.admin_username,
    )
