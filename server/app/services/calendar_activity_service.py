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
    mood_level: int | None = None
    mood_emoji: str | None = None
    events: list[dict] | None = None


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
                select(
                    CalendarEntry.date,
                    func.count(CalendarEntry.id),
                    func.max(CalendarEntry.mood_level),
                )
                .where(
                    CalendarEntry.user_id == user_id,
                    CalendarEntry.date >= start_date,
                    CalendarEntry.date <= last_date,
                )
                .group_by(CalendarEntry.date)
                .order_by(CalendarEntry.date.asc())
            )
        ).all()
        count_map = {
            entry_date: {
                "count": int(count),
                "mood_level": int(mood_level) if mood_level is not None else None,
            }
            for entry_date, count, mood_level in rows
        }
        events_map = await self._build_event_map(user_id=user_id, start_date=start_date, end_date=last_date)

        heatmap: list[CalendarHeatmapItem] = []
        for offset in range(days):
            current_date = start_date + timedelta(days=offset)
            entry_meta = count_map.get(current_date, {"count": 0, "mood_level": None})
            activity_count = entry_meta["count"]
            mood_level = entry_meta["mood_level"]
            heatmap.append(
                CalendarHeatmapItem(
                    date=current_date.isoformat(),
                    activity_count=activity_count,
                    intensity=self._intensity_level(activity_count),
                    mood_level=mood_level,
                    mood_emoji=self._mood_emoji(mood_level),
                    events=events_map.get(current_date.isoformat(), []),
                )
            )
        return heatmap

    async def record_manual_mood(
        self,
        *,
        user_id: int,
        mood_level: int,
        record_date: date | None = None,
    ) -> None:
        target_date = record_date or datetime.now(LOCAL_TZ).date()
        entry = await self.db.scalar(
            select(CalendarEntry).where(
                CalendarEntry.user_id == user_id,
                CalendarEntry.date == target_date,
                CalendarEntry.source == "mood",
            )
        )
        if entry is None:
            self.db.add(
                CalendarEntry(
                    user_id=user_id,
                    date=target_date,
                    mood_level=mood_level,
                    test_record_id=None,
                    source="mood",
                )
            )
        else:
            entry.mood_level = mood_level
        await self.db.flush()

    async def record_activity(
        self,
        *,
        user_id: int,
        source: str,
        activity_date: date | None = None,
        mood_level: int | None = None,
    ) -> None:
        target_date = activity_date or datetime.now(LOCAL_TZ).date()
        if source == "mood":
            await self.record_manual_mood(
                user_id=user_id,
                mood_level=mood_level or 3,
                record_date=target_date,
            )
            return
        self.db.add(
            CalendarEntry(
                user_id=user_id,
                date=target_date,
                mood_level=mood_level,
                test_record_id=None,
                source=source,
            )
        )
        await self.db.flush()

    async def build_stats(self, *, user_id: int, year: int | None = None) -> dict:
        end_date = datetime.now(LOCAL_TZ).date()
        start_date = date(year, 1, 1) if year else end_date - timedelta(days=364)
        entries = list(
            await self.db.scalars(
                select(CalendarEntry)
                .where(
                    CalendarEntry.user_id == user_id,
                    CalendarEntry.date >= start_date,
                    CalendarEntry.date <= end_date,
                )
                .order_by(CalendarEntry.date.asc(), CalendarEntry.id.asc())
            )
        )
        unique_days = sorted({item.date for item in entries})
        active_days = len(unique_days)
        mood_values = [item.mood_level for item in entries if item.mood_level is not None]
        average_mood = round(sum(mood_values) / len(mood_values), 2) if mood_values else 0.0
        current_streak = 0
        cursor = end_date
        unique_day_set = set(unique_days)
        while cursor in unique_day_set:
            current_streak += 1
            cursor = date.fromordinal(cursor.toordinal() - 1)
        best_streak = 0
        streak = 0
        previous_day: date | None = None
        for day in unique_days:
            if previous_day is None or day.toordinal() - previous_day.toordinal() == 1:
                streak += 1
            else:
                streak = 1
            best_streak = max(best_streak, streak)
            previous_day = day
        return {
            "current_streak": current_streak,
            "active_days": active_days,
            "average_mood": average_mood,
            "best_streak": best_streak,
        }

    async def _build_event_map(
        self,
        *,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> dict[str, list[dict]]:
        entries = list(
            await self.db.scalars(
                select(CalendarEntry)
                .where(
                    CalendarEntry.user_id == user_id,
                    CalendarEntry.date >= start_date,
                    CalendarEntry.date <= end_date,
                )
                .order_by(CalendarEntry.date.asc(), CalendarEntry.id.asc())
            )
        )
        events_map: dict[str, list[dict]] = {}
        for entry in entries:
            day_key = entry.date.isoformat()
            events_map.setdefault(day_key, []).append(
                {
                    "source": entry.source,
                    "label": self._source_label(entry.source),
                    "mood_level": entry.mood_level,
                    "emoji": self._source_emoji(entry.source, entry.mood_level),
                }
            )
        return events_map

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

    @staticmethod
    def _mood_emoji(mood_level: int | None) -> str | None:
        mapping = {1: "😔", 2: "😶", 3: "🙂", 4: "😊", 5: "🤩"}
        return mapping.get(mood_level)

    @classmethod
    def _source_emoji(cls, source: str, mood_level: int | None) -> str | None:
        mapping = {
            "test": "🧪",
            "daily_question": cls._mood_emoji(mood_level) or "☀️",
            "fragment": "🧩",
            "mood": cls._mood_emoji(mood_level) or "🙂",
        }
        return mapping.get(source, "•")

    @staticmethod
    def _source_label(source: str) -> str:
        mapping = {
            "test": "完成测试",
            "daily_question": "每日一问",
            "fragment": "灵魂碎片",
            "mood": "手动心情",
        }
        return mapping.get(source, source)
