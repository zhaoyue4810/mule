from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.yaml_loader import yaml_config
from app.models.calendar import CalendarEntry, DailySoulAnswer, DailySoulQuestion
from app.services.badge_unlock_service import BadgeUnlockService


LOCAL_TZ = ZoneInfo("Asia/Shanghai")


@dataclass
class DailyQuestionState:
    question_id: int
    question_text: str
    options: list[str]
    answer_date: str
    answered: bool
    selected_index: int | None
    insight: str | None
    current_streak: int
    best_streak: int
    recent_answered_days: int
    unlocked_badges: list[dict]


class DailyQuestionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_today_question(
        self,
        *,
        user_id: int,
        today: date | None = None,
    ) -> DailyQuestionState:
        await self._ensure_default_questions()
        current_date = today or datetime.now(LOCAL_TZ).date()
        questions = list(
            await self.db.scalars(
                select(DailySoulQuestion).order_by(
                    DailySoulQuestion.sort_order.asc(),
                    DailySoulQuestion.id.asc(),
                )
            )
        )
        if not questions:
            raise LookupError("Daily soul questions are not configured")

        question = questions[(current_date.toordinal() - 1) % len(questions)]
        answer = await self.db.scalar(
            select(DailySoulAnswer).where(
                DailySoulAnswer.user_id == user_id,
                DailySoulAnswer.question_id == question.id,
                DailySoulAnswer.answer_date == current_date,
            )
        )
        selected_index = answer.answer_index if answer else None
        insight = None
        if selected_index is not None:
            insight_map = question.insights or {}
            insight = insight_map.get(str(selected_index)) or insight_map.get(
                str(int(selected_index))
            )
        current_streak, best_streak, recent_answered_days = await self._build_streak_stats(
            user_id=user_id,
            today=current_date,
        )

        return DailyQuestionState(
            question_id=question.id,
            question_text=question.question_text,
            options=list(question.options or []),
            answer_date=current_date.isoformat(),
            answered=answer is not None,
            selected_index=selected_index,
            insight=insight,
            current_streak=current_streak,
            best_streak=best_streak,
            recent_answered_days=recent_answered_days,
            unlocked_badges=[],
        )

    async def submit_answer(
        self,
        *,
        user_id: int,
        question_id: int,
        answer_index: int,
        today: date | None = None,
    ) -> DailyQuestionState:
        current_state = await self.get_today_question(user_id=user_id, today=today)
        if current_state.question_id != question_id:
            raise ValueError("Only today's question can be answered")
        if answer_index < 0 or answer_index >= len(current_state.options):
            raise ValueError("Answer index is out of range")

        current_date = today or datetime.now(LOCAL_TZ).date()
        answer = await self.db.scalar(
            select(DailySoulAnswer).where(
                DailySoulAnswer.user_id == user_id,
                DailySoulAnswer.question_id == question_id,
                DailySoulAnswer.answer_date == current_date,
            )
        )
        if answer is None:
            answer = DailySoulAnswer(
                user_id=user_id,
                question_id=question_id,
                answer_index=answer_index,
                answer_date=current_date,
            )
            self.db.add(answer)
        else:
            answer.answer_index = answer_index

        await self._record_calendar_activity(
            user_id=user_id,
            activity_date=current_date,
            mood_level=answer_index + 1,
        )
        current_streak, best_streak, recent_answered_days = await self._build_streak_stats(
            user_id=user_id,
            today=current_date,
        )
        unlocked_badges = await BadgeUnlockService(self.db).unlock_for_user(
            user_id=user_id,
            unlock_time=datetime.combine(current_date, datetime.min.time(), tzinfo=LOCAL_TZ),
            metrics={
                "daily_streak": current_streak,
                "daily_answer_days": recent_answered_days,
            },
            allowed_rule_types={"daily_streak"},
        )
        await self.db.commit()
        state = await self.get_today_question(user_id=user_id, today=current_date)
        state.unlocked_badges = [
            {
                "badge_key": item.badge_key,
                "name": item.name,
                "emoji": item.emoji,
            }
            for item in unlocked_badges
        ]
        return state

    async def _build_streak_stats(
        self,
        *,
        user_id: int,
        today: date,
    ) -> tuple[int, int, int]:
        answer_dates = list(
            await self.db.scalars(
                select(DailySoulAnswer.answer_date)
                .where(DailySoulAnswer.user_id == user_id)
                .order_by(DailySoulAnswer.answer_date.asc())
            )
        )
        if not answer_dates:
            return 0, 0, 0

        unique_dates = sorted(set(answer_dates))
        date_set = set(unique_dates)

        current_streak = 0
        cursor = today
        while cursor in date_set:
            current_streak += 1
            cursor = date.fromordinal(cursor.toordinal() - 1)

        best_streak = 0
        streak = 0
        previous_date: date | None = None
        for answer_date in unique_dates:
            if previous_date is None or (
                answer_date.toordinal() - previous_date.toordinal() == 1
            ):
                streak += 1
            else:
                streak = 1
            best_streak = max(best_streak, streak)
            previous_date = answer_date

        recent_answered_days = sum(
            1 for item in unique_dates if 0 <= today.toordinal() - item.toordinal() < 7
        )
        return current_streak, best_streak, recent_answered_days

    async def _record_calendar_activity(
        self,
        *,
        user_id: int,
        activity_date: date,
        mood_level: int,
    ) -> None:
        entry = await self.db.scalar(
            select(CalendarEntry).where(
                CalendarEntry.user_id == user_id,
                CalendarEntry.date == activity_date,
                CalendarEntry.source == "daily_question",
            )
        )
        if entry is None:
            self.db.add(
                CalendarEntry(
                    user_id=user_id,
                    date=activity_date,
                    mood_level=mood_level,
                    test_record_id=None,
                    source="daily_question",
                )
            )
        else:
            entry.mood_level = mood_level
        await self.db.flush()

    async def _ensure_default_questions(self) -> None:
        question_count = int(
            await self.db.scalar(select(func.count(DailySoulQuestion.id))) or 0
        )
        if question_count > 0:
            return

        if not yaml_config._store:
            yaml_config.load_all()

        questions = yaml_config._store.get("daily_questions", {}).get("questions", [])
        for sort_order, item in enumerate(questions, start=1):
            insights = item.get("insights") or {
                str(index): option for index, option in enumerate(item.get("options", []))
            }
            self.db.add(
                DailySoulQuestion(
                    question_text=item["text"],
                    options=item.get("options", []),
                    insights=insights,
                    sort_order=sort_order,
                    yaml_source="daily_questions.yaml",
                )
            )
        await self.db.flush()
