from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import CalendarEntry


LOCAL_TZ = ZoneInfo("Asia/Shanghai")


@dataclass
class CalendarHeatmapItem:
    date: str
    activity_count: int
    intensity: int


class CalendarActivityService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_test_completion(
        self,
        *,
        user_id: int,
        test_record_id: int,
        completed_at: datetime | None = None,
    ) -> None:
        local_date = (completed_at or datetime.now()).astimezone(LOCAL_TZ).date()
        self.db.add(
            CalendarEntry(
                user_id=user_id,
                date=local_date,
                mood_level=None,
                test_record_id=test_record_id,
                source="test",
            )
        )
        await self.db.flush()

    async def build_heatmap(
        self,
        *,
        user_id: int,
        days: int = 30,
        end_date: date | None = None,
    ) -> list[CalendarHeatmapItem]:
        if days <= 0:
            return []

        last_date = end_date or datetime.now(LOCAL_TZ).date()
        start_date = last_date - timedelta(days=days - 1)
        rows = (
            await self.db.execute(
                select(CalendarEntry.date, func.count(CalendarEntry.id))
                .where(
                    CalendarEntry.user_id == user_id,
                    CalendarEntry.date >= start_date,
                    CalendarEntry.date <= last_date,
                )
                .group_by(CalendarEntry.date)
                .order_by(CalendarEntry.date.asc())
            )
        ).all()
        count_map = {entry_date: int(count) for entry_date, count in rows}

        heatmap: list[CalendarHeatmapItem] = []
        for offset in range(days):
            current_date = start_date + timedelta(days=offset)
            activity_count = count_map.get(current_date, 0)
            heatmap.append(
                CalendarHeatmapItem(
                    date=current_date.isoformat(),
                    activity_count=activity_count,
                    intensity=self._intensity_level(activity_count),
                )
            )
        return heatmap

    @staticmethod
    def _intensity_level(activity_count: int) -> int:
        if activity_count <= 0:
            return 0
        if activity_count == 1:
            return 1
        if activity_count == 2:
            return 2
        if activity_count == 3:
            return 3
        return 4
