from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import BadgeDefinition, UserBadge
from app.models.record import TestRecord
from app.models.report import ReportSnapshot
from app.models.test import Test
from app.models.user import User
from app.services.calendar_activity_service import CalendarActivityService
from app.services.soul_fragment_service import SoulFragmentService


class AppProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_onboarding_profile(self, user_id: int) -> dict:
        user = await self._get_user(user_id)
        return {
            "nickname": user.nickname,
            "avatar_value": user.avatar_value,
            "bio": user.bio,
            "gender": user.gender,
            "birth_year": user.birth_year,
            "birth_month": user.birth_month,
            "onboarding_completed": user.onboarding_completed,
        }

    async def update_onboarding_profile(self, user_id: int, payload) -> dict:
        user = await self._get_user(user_id)
        nickname = payload.nickname.strip()
        avatar_value = payload.avatar_value.strip()
        bio = payload.bio.strip()

        if not nickname:
            raise ValueError("Nickname is required")
        if len(nickname) > 20:
            raise ValueError("Nickname must be 20 characters or fewer")
        if not avatar_value:
            raise ValueError("Avatar value is required")
        if len(bio) > 80:
            raise ValueError("Bio must be 80 characters or fewer")
        if payload.gender not in {0, 1, 2}:
            raise ValueError("Gender must be 0, 1 or 2")
        if payload.birth_year is not None:
            current_year = datetime.now().year
            if payload.birth_year < 1900 or payload.birth_year > current_year:
                raise ValueError("Birth year is out of range")
        if payload.birth_month is not None and not 1 <= payload.birth_month <= 12:
            raise ValueError("Birth month must be between 1 and 12")

        user.nickname = nickname
        user.avatar_value = avatar_value
        user.bio = bio
        user.gender = payload.gender
        user.birth_year = payload.birth_year
        user.birth_month = payload.birth_month
        user.onboarding_completed = True

        await self.db.commit()
        await self.db.refresh(user)
        return await self.get_onboarding_profile(user_id)

    async def get_settings(self, user_id: int) -> dict:
        user = await self._get_user(user_id)
        return {
            "sound_enabled": bool(user.sound_enabled),
        }

    async def update_settings(self, user_id: int, payload) -> dict:
        user = await self._get_user(user_id)
        user.sound_enabled = bool(payload.sound_enabled)
        await self.db.commit()
        await self.db.refresh(user)
        return await self.get_settings(user_id)

    async def get_overview(self, user_id: int) -> dict:
        user = await self._get_user(user_id)
        history = await self._get_report_history(user_id)

        durations = [
            item["duration_seconds"]
            for item in history
            if isinstance(item["duration_seconds"], int)
        ]
        avg_duration_seconds = round(sum(durations) / len(durations)) if durations else 0

        dimension_totals: dict[str, float] = defaultdict(float)
        persona_totals: dict[tuple[str | None, str | None], int] = defaultdict(int)
        distinct_test_codes: set[str] = set()

        for item in history:
            distinct_test_codes.add(item["test_code"])
            if item["persona_key"] or item["persona_name"]:
                persona_totals[(item["persona_key"], item["persona_name"])] += 1

            for dim_code, score in item["dimension_scores"].items():
                dimension_totals[dim_code] += score

        dominant_dimensions = [
            {
                "dim_code": dim_code,
                "total_score": round(score, 4),
            }
            for dim_code, score in sorted(
                dimension_totals.items(),
                key=lambda item: abs(item[1]),
                reverse=True,
            )[:5]
        ]
        persona_distribution = [
            {
                "persona_key": persona_key,
                "persona_name": persona_name,
                "count": count,
            }
            for (persona_key, persona_name), count in sorted(
                persona_totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:5]
        ]
        badges = await self._get_badges(user_id)
        calendar_heatmap = await CalendarActivityService(self.db).build_heatmap(
            user_id=user_id,
            days=30,
        )
        soul_fragment_service = SoulFragmentService(self.db)
        soul_fragments = await soul_fragment_service.list_user_fragments(user_id)
        fragment_progress = await soul_fragment_service.build_category_progress(user_id)
        fragment_map = await soul_fragment_service.build_fragment_map(user_id)

        return {
            "user_id": user.id,
            "nickname": user.nickname,
            "avatar_value": user.avatar_value,
            "test_count": len(history),
            "distinct_test_count": len(distinct_test_codes),
            "avg_duration_seconds": avg_duration_seconds,
            "last_test_at": history[0]["completed_at"] if history else None,
            "dominant_dimensions": dominant_dimensions,
            "persona_distribution": persona_distribution,
            "badges": badges,
            "calendar_heatmap": [
                {
                    "date": item.date,
                    "activity_count": item.activity_count,
                    "intensity": item.intensity,
                }
                for item in calendar_heatmap
            ],
            "soul_fragments": soul_fragments,
            "fragment_progress": fragment_progress,
            "fragment_map": fragment_map,
            "recent_reports": [
                self._to_history_payload(item) for item in history[:3]
            ],
        }

    async def list_reports(self, user_id: int) -> list[dict]:
        await self._get_user(user_id)
        history = await self._get_report_history(user_id)
        return [self._to_history_payload(item) for item in history]

    async def _get_user(self, user_id: int) -> User:
        user = await self.db.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise LookupError(f"User not found: {user_id}")
        return user

    async def _get_report_history(self, user_id: int) -> list[dict]:
        query = (
            select(TestRecord, Test, ReportSnapshot)
            .join(Test, Test.id == TestRecord.test_id)
            .outerjoin(ReportSnapshot, ReportSnapshot.record_id == TestRecord.id)
            .where(TestRecord.user_id == user_id)
            .order_by(TestRecord.created_at.desc(), TestRecord.id.desc())
        )
        rows = (await self.db.execute(query)).all()

        history: list[dict] = []
        for record, test, snapshot in rows:
            report_json = snapshot.report_json if snapshot else {}
            dimension_scores = {
                str(dim_code): float(score)
                for dim_code, score in (snapshot.dimension_scores or {}).items()
            } if snapshot else {}

            history.append(
                {
                    "record_id": record.id,
                    "test_code": test.test_code,
                    "test_name": test.title,
                    "persona_key": report_json.get("persona_key"),
                    "persona_name": report_json.get("persona_name"),
                    "summary": report_json.get("summary", ""),
                    "total_score": snapshot.overall_score if snapshot else record.total_score,
                    "duration_seconds": record.duration,
                    "completed_at": record.created_at,
                    "dimension_scores": dimension_scores,
                }
            )

        return history

    def _to_history_payload(self, item: dict) -> dict:
        return {
            "record_id": item["record_id"],
            "test_code": item["test_code"],
            "test_name": item["test_name"],
            "persona_key": item["persona_key"],
            "persona_name": item["persona_name"],
            "summary": item["summary"],
            "total_score": item["total_score"],
            "duration_seconds": item["duration_seconds"],
            "completed_at": item["completed_at"],
        }

    async def _get_badges(self, user_id: int) -> list[dict]:
        rows = (
            await self.db.execute(
                select(UserBadge, BadgeDefinition)
                .join(BadgeDefinition, BadgeDefinition.id == UserBadge.badge_id)
                .where(UserBadge.user_id == user_id)
                .order_by(UserBadge.created_at.desc(), UserBadge.id.desc())
            )
        ).all()
        return [
            {
                "badge_key": badge.badge_key,
                "name": badge.name,
                "emoji": badge.emoji,
                "tier": user_badge.tier,
                "unlock_count": user_badge.unlock_count,
                "unlocked_at": user_badge.created_at,
            }
            for user_badge, badge in rows
        ]
