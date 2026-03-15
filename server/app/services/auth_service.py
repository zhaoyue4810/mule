from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import httpx
from redis import asyncio as redis_asyncio
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.badge import UserBadge
from app.models.calendar import CalendarEntry, DailySoulAnswer
from app.models.record import TestRecord
from app.models.soul import TimeCapsule, UserSoulFragment
from app.models.user import User
from app.models.user import UserMemory, UserSetting
from app.services.sms_service import create_sms_sender, generate_code


PHONE_PATTERN = re.compile(r"^1\d{10}$")
_MEMORY_CODE_STORE: dict[str, tuple[str, datetime]] = {}
_MEMORY_SMS_LIMIT_STORE: dict[str, datetime] = {}


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    async def create_guest_session(self, nickname: str | None = None) -> dict:
        user = User(
            nickname=(nickname or "").strip() or "访客用户",
            avatar_value="🧠",
            onboarding_completed=False,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return self._build_session_payload(user)

    async def create_session_for_user(self, user: User) -> dict:
        return self._build_session_payload(user)

    async def send_phone_code(self, phone: str) -> dict:
        normalized_phone = self._normalize_phone(phone)
        await self._enforce_phone_send_rate_limit(normalized_phone)
        code = self._generate_phone_code()
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.settings.sms_code_expire_seconds
        )
        delivery = await self._deliver_phone_code(normalized_phone, code)
        await self._store_phone_code(normalized_phone, code, expires_at)
        await self._store_phone_send_limit(normalized_phone)
        return {
            "phone": normalized_phone,
            "expires_in_seconds": self.settings.sms_code_expire_seconds,
            "provider": delivery["provider"],
            "debug_code": code if self.settings.app_env != "production" else None,
        }

    async def login_with_phone(
        self,
        *,
        phone: str,
        code: str,
        current_user: User | None = None,
    ) -> dict:
        normalized_phone = self._normalize_phone(phone)
        await self._verify_phone_code(normalized_phone, code)

        phone_user = await self.db.scalar(
            select(User).where(User.phone == normalized_phone)
        )
        if current_user is not None:
            if phone_user is None:
                current_user.phone = normalized_phone
                await self.db.commit()
                await self.db.refresh(current_user)
                return self._build_session_payload(current_user)

            if phone_user.id == current_user.id:
                return self._build_session_payload(phone_user)

            await self._merge_user_assets(source_user=current_user, target_user=phone_user)
            return self._build_session_payload(phone_user)

        if phone_user is None:
            phone_user = User(
                phone=normalized_phone,
                nickname="手机号用户",
                avatar_value="🧠",
                onboarding_completed=False,
            )
            self.db.add(phone_user)
            await self.db.commit()
            await self.db.refresh(phone_user)
            return self._build_session_payload(phone_user)

        return self._build_session_payload(phone_user)

    async def login_with_wechat_mini_program(
        self,
        *,
        code: str,
        nickname: str | None = None,
        avatar_value: str | None = None,
        current_user: User | None = None,
    ) -> dict:
        if not self.settings.wx_appid or not self.settings.wx_secret:
            raise RuntimeError(
                "WeChat mini program credentials are not configured yet"
            )

        session_data = await self._exchange_wechat_code(code)
        openid = str(session_data.get("openid") or "").strip()
        if not openid:
            raise RuntimeError("WeChat login response missing openid")

        unionid = str(session_data.get("unionid") or "").strip() or None

        user = await self._find_wechat_user(openid=openid, unionid=unionid)
        if current_user is not None:
            if user is None:
                user = current_user
            elif user.id != current_user.id:
                await self._merge_user_assets(source_user=current_user, target_user=user)

        if user is None:
            user = User(
                openid=openid,
                unionid=unionid,
                nickname=(nickname or "").strip() or "微信用户",
                avatar_value=(avatar_value or "").strip() or "🧠",
                onboarding_completed=False,
            )
            self.db.add(user)
        else:
            user.openid = openid
            if unionid:
                user.unionid = unionid
            if nickname and nickname.strip():
                user.nickname = nickname.strip()
            if avatar_value and avatar_value.strip():
                user.avatar_value = avatar_value.strip()

        await self.db.commit()
        await self.db.refresh(user)
        return self._build_session_payload(user)

    async def _find_wechat_user(
        self,
        *,
        openid: str,
        unionid: str | None,
    ) -> User | None:
        if unionid:
            user = await self.db.scalar(select(User).where(User.unionid == unionid))
            if user is not None:
                return user
        return await self.db.scalar(select(User).where(User.openid == openid))

    async def _exchange_wechat_code(self, code: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": self.settings.wx_appid,
                    "secret": self.settings.wx_secret,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            payload = response.json()

        if payload.get("errcode"):
            raise RuntimeError(
                f"WeChat login failed: {payload.get('errmsg') or payload['errcode']}"
            )
        return payload

    def _normalize_phone(self, phone: str) -> str:
        normalized = "".join(ch for ch in phone if ch.isdigit())
        if not PHONE_PATTERN.match(normalized):
            raise ValueError("Invalid phone number")
        return normalized

    def _generate_phone_code(self) -> str:
        fixed_code = (self.settings.sms_debug_fixed_code or "").strip()
        if self.settings.app_env != "production" and fixed_code:
            return fixed_code
        return generate_code()

    async def _deliver_phone_code(self, phone: str, code: str) -> dict:
        provider = (self.settings.sms_provider or "mock").strip().lower()
        sender = create_sms_sender(
            provider=provider,
            access_key=self.settings.aliyun_sms_access_key,
            secret=self.settings.aliyun_sms_secret,
            sign_name=self.settings.aliyun_sms_sign_name,
            template_code=self.settings.aliyun_sms_template_code,
        )
        accepted = await sender.send_code(phone, code)
        if not accepted:
            raise RuntimeError("Failed to send SMS verification code")
        return {"provider": provider, "phone": phone, "accepted": accepted}

    async def _store_phone_code(
        self,
        phone: str,
        code: str,
        expires_at: datetime,
    ) -> None:
        cache_key = self._phone_code_cache_key(phone)
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                ttl_seconds = max(
                    1,
                    int((expires_at - datetime.now(timezone.utc)).total_seconds()),
                )
                await redis_client.set(cache_key, code, ex=ttl_seconds)
                return
            except Exception:
                pass

        _MEMORY_CODE_STORE[cache_key] = (code, expires_at)

    async def _store_phone_send_limit(self, phone: str) -> None:
        cache_key = self._phone_limit_cache_key(phone)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=60)
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                await redis_client.set(cache_key, "1", ex=60)
                return
            except Exception:
                pass

        _MEMORY_SMS_LIMIT_STORE[cache_key] = expires_at

    async def _enforce_phone_send_rate_limit(self, phone: str) -> None:
        cache_key = self._phone_limit_cache_key(phone)
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                if await redis_client.exists(cache_key):
                    raise ValueError("Please wait 60 seconds before requesting another code")
                return
            except ValueError:
                raise
            except Exception:
                pass

        expires_at = _MEMORY_SMS_LIMIT_STORE.get(cache_key)
        if expires_at and expires_at >= datetime.now(timezone.utc):
            raise ValueError("Please wait 60 seconds before requesting another code")
        if expires_at:
            _MEMORY_SMS_LIMIT_STORE.pop(cache_key, None)

    async def _verify_phone_code(self, phone: str, code: str) -> None:
        cache_key = self._phone_code_cache_key(phone)
        expected_code = None
        redis_client = self._get_redis_client()
        if redis_client is not None:
            try:
                raw = await redis_client.get(cache_key)
                if raw is not None:
                    expected_code = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                    await redis_client.delete(cache_key)
            except Exception:
                expected_code = None

        if expected_code is None:
            value = _MEMORY_CODE_STORE.pop(cache_key, None)
            if value is not None:
                memory_code, expires_at = value
                if expires_at >= datetime.now(timezone.utc):
                    expected_code = memory_code

        if expected_code is None:
            raise ValueError("Verification code expired")
        if expected_code != code.strip():
            raise ValueError("Invalid verification code")

    async def _merge_user_assets(self, source_user: User, target_user: User) -> None:
        if source_user.id == target_user.id:
            return

        for model in (
            TestRecord,
            CalendarEntry,
            DailySoulAnswer,
            UserBadge,
            TimeCapsule,
            UserSoulFragment,
        ):
            await self.db.execute(
                update(model)
                .where(model.user_id == source_user.id)
                .values(user_id=target_user.id)
            )

        await self.db.execute(delete(UserSetting).where(UserSetting.user_id == source_user.id))
        await self.db.execute(delete(UserMemory).where(UserMemory.user_id == source_user.id))
        await self.db.execute(delete(User).where(User.id == source_user.id))
        await self.db.commit()

    def _phone_code_cache_key(self, phone: str) -> str:
        return f"sms:{phone}"

    def _phone_limit_cache_key(self, phone: str) -> str:
        return f"sms_limit:{phone}"

    def _get_redis_client(self):
        try:
            return redis_asyncio.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=False,
            )
        except Exception:
            return None

    def _build_session_payload(self, user: User) -> dict:
        access_token, expires_at = create_access_token(user_id=user.id)
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_at": expires_at,
            "user": {
                "user_id": user.id,
                "nickname": user.nickname,
                "avatar_value": user.avatar_value,
                "onboarding_completed": user.onboarding_completed,
                "is_guest": not bool(user.openid or user.phone),
                "has_openid": bool(user.openid),
                "has_phone": bool(user.phone),
                "masked_phone": self._mask_phone(user.phone),
            },
        }

    def _mask_phone(self, phone: str | None) -> str | None:
        if not phone:
            return None
        if len(phone) < 7:
            return phone
        return f"{phone[:3]}****{phone[-4:]}"
