from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))


def create_access_token(*, user_id: int) -> tuple[str, datetime]:
    return create_signed_token(payload={"sub": str(user_id), "typ": "access"})


def create_admin_token(*, username: str) -> tuple[str, datetime]:
    return create_signed_token(payload={"sub": username, "typ": "admin"})


def create_signed_token(*, payload: dict[str, object]) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {**payload, "exp": int(expires_at.timestamp())}
    payload_bytes = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}", expires_at


def decode_access_token(token: str) -> dict[str, object]:
    return decode_signed_token(token, expected_type="access")


def decode_admin_token(token: str) -> dict[str, object]:
    return decode_signed_token(token, expected_type="admin")


def decode_signed_token(token: str, *, expected_type: str | None = None) -> dict[str, object]:
    settings = get_settings()
    try:
        payload_part, signature_part = token.split(".", 1)
        payload_bytes = _b64url_decode(payload_part)
        signature = _b64url_decode(signature_part)
    except Exception as exc:  # pragma: no cover - defensive parsing
        raise ValueError("Invalid token format") from exc

    expected_signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(payload_bytes.decode("utf-8"))
    token_type = payload.get("typ")
    if expected_type and token_type != expected_type:
        raise ValueError("Unsupported token type")

    expires_at = int(payload.get("exp") or 0)
    if expires_at <= int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Token expired")

    return payload
