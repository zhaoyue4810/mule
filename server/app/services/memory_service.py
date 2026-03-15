from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import TestRecord
from app.models.report import ReportSnapshot
from app.models.test import Question, Test, TestVersion
from app.models.user import User, UserMemory

LOCAL_TZ = ZoneInfo("Asia/Shanghai")

class MemoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def update_memory_for_record(self, *, user_id: int, record_id: int) -> None:
        rows = (
            await self.db.execute(
                select(TestRecord, Test, ReportSnapshot)
                .join(Test, Test.id == TestRecord.test_id)
                .outerjoin(ReportSnapshot, ReportSnapshot.record_id == TestRecord.id)
                .where(TestRecord.user_id == user_id)
                .order_by(TestRecord.created_at.asc(), TestRecord.id.asc())
            )
        ).all()
        if not rows:
            return

        memory = await self.db.scalar(select(UserMemory).where(UserMemory.user_id == user_id))
        if memory is None:
            memory = UserMemory(user_id=user_id)
            self.db.add(memory)

        category_counts = Counter((test.category or "").strip() for _, test, _ in rows if test.category)
        avg_duration = round(
            sum((record.duration or 0) for record, _, _ in rows) / max(1, len(rows))
        )
        avg_score = round(
            sum(float(snapshot.overall_score or record.total_score or 0) for record, _, snapshot in rows)
            / max(1, len(rows)),
            2,
        )
        favorite_categories = [
            category
            for category, _ in category_counts.most_common(2)
            if category
        ]
        last_record = rows[-1][0]

        memory.test_count = len(rows)
        memory.avg_duration = avg_duration
        memory.avg_score = avg_score
        memory.fav_categories = favorite_categories
        memory.know_level = self._resolve_level(len(rows))
        memory.last_test_at = self._as_naive_utc(last_record.created_at)
        await self.db.flush()

    async def get_greeting(self, *, user: User) -> dict:
        memory = await self._get_or_build_memory(user.id)
        tags = await self._detect_behavior_tags(user_id=user.id, memory=memory)
        mood, greeting = self._build_greeting(tags, memory.test_count)
        return {
            "greeting": greeting,
            "mood": mood,
            "know_level": memory.know_level,
            "test_count": memory.test_count,
            "behavior_tags": tags,
        }

    async def get_suggestions(self, *, user: User) -> dict:
        memory = await self._get_or_build_memory(user.id)
        tags = await self._detect_behavior_tags(user_id=user.id, memory=memory)
        completed_rows = (
            await self.db.execute(
                select(Test.test_code, Test.category)
                .join(TestRecord, TestRecord.test_id == Test.id)
                .where(TestRecord.user_id == user.id)
            )
        ).all()
        completed_codes = {str(test_code) for test_code, _ in completed_rows}
        recent_categories = [str(category) for _, category in completed_rows[-3:] if category]

        version_subquery = (
            select(TestVersion.test_id, TestVersion.version, TestVersion.duration_hint)
            .where(TestVersion.status == "PUBLISHED")
            .subquery()
        )
        tests = (
            await self.db.execute(
                select(Test, version_subquery.c.version, version_subquery.c.duration_hint)
                .join(version_subquery, version_subquery.c.test_id == Test.id)
                .order_by(Test.sort_order.asc(), Test.id.asc())
            )
        ).all()

        prioritized: list[dict] = []
        fallback: list[dict] = []
        for test, version, duration_hint in tests:
            payload = {
                "test_code": test.test_code,
                "name": test.title,
                "category": test.category,
                "is_match_enabled": test.is_match_enabled,
                "participant_count": test.participant_count,
                "version": int(version),
                "question_count": await self._question_count_for_test(test.id),
                "duration_hint": duration_hint,
                "cover_gradient": None,
            }
            if test.test_code not in completed_codes and test.category not in recent_categories:
                prioritized.append(payload)
            elif test.test_code not in completed_codes:
                fallback.append(payload)
        items = (prioritized + fallback)[:3]

        reason = "优先推荐你还没完成、且最近没刷过同类的测试。"
        if "关系控" in tags:
            reason = "最近你更关注关系主题，所以我把关系之外的内容也插进来，保持探索新鲜感。"
        elif "性格控" in tags:
            reason = "你明显对性格画像更有兴趣，这次优先补上不同分类，帮你看见更多侧面。"
        return {
            "title": "小测替你挑了下一站",
            "reason": reason,
            "items": items,
        }

    async def _get_or_build_memory(self, user_id: int) -> UserMemory:
        memory = await self.db.scalar(select(UserMemory).where(UserMemory.user_id == user_id))
        if memory is not None:
            return memory
        await self.update_memory_for_record(user_id=user_id, record_id=0)
        memory = await self.db.scalar(select(UserMemory).where(UserMemory.user_id == user_id))
        if memory is None:
            memory = UserMemory(user_id=user_id)
            self.db.add(memory)
            await self.db.flush()
        return memory

    async def _detect_behavior_tags(self, *, user_id: int, memory: UserMemory) -> list[str]:
        rows = (
            await self.db.execute(
                select(TestRecord, Test)
                .join(Test, Test.id == TestRecord.test_id)
                .where(TestRecord.user_id == user_id)
                .order_by(TestRecord.created_at.asc(), TestRecord.id.asc())
            )
        ).all()
        if not rows:
            return []

        tags: list[str] = []
        hour_counter = Counter(self._as_local_hour(record.created_at) for record, _ in rows)
        if sum(count for hour, count in hour_counter.items() if hour >= 22 or hour <= 4) >= 1:
            tags.append("夜猫子")
        if sum(count for hour, count in hour_counter.items() if 5 <= hour <= 8) >= 1:
            tags.append("早起鸟")

        category_counter = Counter((test.category or "").strip() for _, test in rows if test.category)
        total = len(rows)
        if total and category_counter.get("personality", 0) / total > 0.5:
            tags.append("性格控")
        if total and category_counter.get("relationship", 0) / total > 0.5:
            tags.append("关系控")

        durations_per_question = []
        for record, test in rows:
            question_count = await self._question_count_for_test(test.id)
            if question_count > 0 and record.duration:
                durations_per_question.append(record.duration / question_count)
        if durations_per_question:
            average = sum(durations_per_question) / len(durations_per_question)
            if average < 30:
                tags.append("闪电侠")
            if average > 60:
                tags.append("思考者")

        if memory.avg_score > 82:
            tags.append("高分选手")
        if len(rows) >= 2:
            previous = rows[-2][0].created_at
            latest = rows[-1][0].created_at
            if latest and previous and self._as_utc(latest) - self._as_utc(previous) > timedelta(days=3):
                tags.append("回归用户")
        return tags

    async def _question_count_for_test(self, test_id: int) -> int:
        row = (await self.db.execute(
            select(TestVersion.id).where(
                TestVersion.test_id == test_id,
                TestVersion.status == "PUBLISHED",
            )
        )).first()
        if row is None:
            return 0
        version_id = int(row[0])
        return int(
            await self.db.scalar(
                select(func.count(Question.id)).where(Question.version_id == version_id)
            )
            or 0
        )

    def _build_greeting(self, tags: list[str], test_count: int) -> tuple[str, str]:
        if "回归用户" in tags:
            return "love", "隔了几天再回来，像给灵魂续上了新的章节。"
        if "夜猫子" in tags:
            return "thinking", "又在夜色里来找小测了，今晚的你很适合做一份更诚实的自我探索。"
        if "早起鸟" in tags:
            return "happy", "你总是在清晨状态最清透的时候出现，今天也很适合点亮新的切面。"
        if "闪电侠" in tags:
            return "cheer", "你做决定很干脆，小测已经记住这种利落的节奏了。"
        if "思考者" in tags:
            return "thinking", "你每次都愿意多停留几秒，这种认真会让画像越来越稳。"
        if test_count >= 6:
            return "happy", "我们已经一起走过不少测试了，小测开始越来越懂你。"
        return "cheer", "今天想从哪一道问题开始，继续把你的灵魂地图拼完整？"

    @staticmethod
    def _resolve_level(test_count: int) -> int:
        if test_count <= 0:
            return 0
        if test_count <= 2:
            return 1
        if test_count <= 5:
            return 2
        if test_count <= 8:
            return 3
        if test_count <= 11:
            return 4
        return 5

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _as_naive_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    def _as_local_hour(self, value: datetime | None) -> int:
        if value is None:
            return 12
        return self._as_utc(value).astimezone(LOCAL_TZ).hour
