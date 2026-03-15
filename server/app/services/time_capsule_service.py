from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import TestRecord
from app.models.report import ReportSnapshot
from app.models.soul import TimeCapsule
from app.models.test import Test, TestPersona
from app.models.user import User
from app.services.content_filter import ContentFilterError, check_text


ALLOWED_CAPSULE_DURATIONS = {30, 90, 365}


@dataclass
class TimeCapsulePayload:
    id: int
    message: str
    persona_title: str | None
    persona_icon: str | None
    test_id: int | None
    report_id: int | None
    created_at: datetime
    unlock_date: date
    duration_days: int
    is_read: bool
    is_unlocked: bool
    days_remaining: int


class TimeCapsuleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_capsule(
        self,
        *,
        user: User,
        message: str,
        duration_days: int,
        report_id: int,
        today: date | None = None,
    ) -> dict:
        normalized_message = message.strip()
        if not normalized_message:
            raise ValueError("Capsule message is required")
        if not check_text(normalized_message).passed:
            raise ContentFilterError("内容包含不当信息，请修改后重试")
        if len(normalized_message) > 1000:
            raise ValueError("Capsule message must be 1000 characters or fewer")
        if duration_days not in ALLOWED_CAPSULE_DURATIONS:
            raise ValueError("Capsule duration must be 30, 90 or 365 days")

        report, record, test, persona = await self._get_report_bundle(report_id=report_id)
        if record.user_id != user.id:
            raise LookupError(f"Report not found: {report_id}")

        current_date = today or datetime.now().date()
        capsule = TimeCapsule(
            user_id=user.id,
            message=normalized_message,
            persona_title=persona.persona_name if persona else report.report_json.get("persona_name"),
            persona_icon=persona.emoji if persona else None,
            test_id=test.id if test else None,
            report_id=report.id,
            duration_days=duration_days,
            unlock_date=current_date + timedelta(days=duration_days),
            is_read=False,
        )
        self.db.add(capsule)
        await self.db.commit()
        await self.db.refresh(capsule)
        return self._serialize_item(capsule, today=current_date).__dict__

    async def list_capsules(self, *, user: User, today: date | None = None) -> list[dict]:
        items = list(
            await self.db.scalars(
                select(TimeCapsule)
                .where(TimeCapsule.user_id == user.id)
                .order_by(TimeCapsule.created_at.desc(), TimeCapsule.id.desc())
            )
        )
        return [self._serialize_item(item, today=today).__dict__ for item in items]

    async def reveal_capsule(
        self,
        *,
        user: User,
        capsule_id: int,
        today: date | None = None,
    ) -> dict:
        item = await self.db.scalar(
            select(TimeCapsule).where(
                TimeCapsule.id == capsule_id,
                TimeCapsule.user_id == user.id,
            )
        )
        if item is None:
            raise LookupError(f"Time capsule not found: {capsule_id}")

        current_date = today or datetime.now().date()
        if item.unlock_date > current_date:
            raise ValueError("This capsule is still locked")

        item.is_read = True
        await self.db.commit()
        await self.db.refresh(item)
        return self._serialize_item(item, today=current_date).__dict__

    async def check_revealable(self, *, user: User, today: date | None = None) -> dict:
        current_date = today or datetime.now().date()
        items = list(
            await self.db.scalars(
                select(TimeCapsule)
                .where(
                    TimeCapsule.user_id == user.id,
                    TimeCapsule.unlock_date <= current_date,
                    TimeCapsule.is_read.is_(False),
                )
                .order_by(TimeCapsule.unlock_date.asc(), TimeCapsule.id.asc())
            )
        )
        return {
            "has_revealable": bool(items),
            "items": [self._serialize_item(item, today=current_date).__dict__ for item in items],
        }

    async def _get_report_bundle(
        self,
        *,
        report_id: int,
    ) -> tuple[ReportSnapshot, TestRecord, Test | None, TestPersona | None]:
        report = await self.db.scalar(select(ReportSnapshot).where(ReportSnapshot.id == report_id))
        if report is None:
            raise LookupError(f"Report not found: {report_id}")
        record = await self.db.scalar(select(TestRecord).where(TestRecord.id == report.record_id))
        if record is None:
            raise LookupError(f"Test record not found: {report.record_id}")
        test = await self.db.scalar(select(Test).where(Test.id == record.test_id))
        persona = None
        if report.persona_code:
            persona = await self.db.scalar(
                select(TestPersona).where(
                    TestPersona.version_id == record.version_id,
                    TestPersona.persona_key == report.persona_code,
                )
            )
        return report, record, test, persona

    def _serialize_item(self, item: TimeCapsule, *, today: date | None = None) -> TimeCapsulePayload:
        current_date = today or datetime.now().date()
        is_unlocked = item.unlock_date <= current_date
        remaining = max(0, (item.unlock_date - current_date).days)
        return TimeCapsulePayload(
            id=item.id,
            message=item.message,
            persona_title=item.persona_title,
            persona_icon=item.persona_icon,
            test_id=item.test_id,
            report_id=item.report_id,
            created_at=item.created_at,
            unlock_date=item.unlock_date,
            duration_days=item.duration_days,
            is_read=item.is_read,
            is_unlocked=is_unlocked,
            days_remaining=remaining,
        )
