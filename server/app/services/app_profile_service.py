from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import TestRecord
from app.models.report import ReportSnapshot
from app.models.test import Test
from app.models.user import User


class AppProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
