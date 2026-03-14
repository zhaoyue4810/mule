import asyncio
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_metadata
from app.core.yaml_loader import yaml_config
from app.models.calendar import CalendarEntry
from app.services.daily_question_service import DailyQuestionService


def test_get_today_question_is_stable_for_same_day() -> None:
    asyncio.run(_test_get_today_question_is_stable_for_same_day())


async def _test_get_today_question_is_stable_for_same_day() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        yaml_config.load_all()
        async with session_factory() as session:
            service = DailyQuestionService(session)
            first = await service.get_today_question(user_id=1, today=date(2026, 3, 14))
            second = await service.get_today_question(user_id=1, today=date(2026, 3, 14))

            assert first.question_id == second.question_id
            assert first.question_text == second.question_text
            assert first.answered is False
    finally:
        await engine.dispose()


def test_submit_daily_question_records_answer_and_calendar_entry() -> None:
    asyncio.run(_test_submit_daily_question_records_answer_and_calendar_entry())


async def _test_submit_daily_question_records_answer_and_calendar_entry() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        yaml_config.load_all()
        async with session_factory() as session:
            service = DailyQuestionService(session)
            question = await service.get_today_question(user_id=2, today=date(2026, 3, 14))
            answered = await service.submit_answer(
                user_id=2,
                question_id=question.question_id,
                answer_index=1,
                today=date(2026, 3, 14),
            )
            calendar_entry = await session.scalar(
                select(CalendarEntry).where(
                    CalendarEntry.user_id == 2,
                    CalendarEntry.source == "daily_question",
                )
            )

            assert answered.answered is True
            assert answered.selected_index == 1
            assert answered.insight
            assert answered.current_streak == 1
            assert answered.best_streak == 1
            assert answered.recent_answered_days == 1
            assert answered.unlocked_badges == []
            assert calendar_entry is not None
            assert calendar_entry.mood_level == 2
    finally:
        await engine.dispose()


def test_daily_question_streak_counts_consecutive_days() -> None:
    asyncio.run(_test_daily_question_streak_counts_consecutive_days())


async def _test_daily_question_streak_counts_consecutive_days() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        yaml_config.load_all()
        async with session_factory() as session:
            service = DailyQuestionService(session)
            first = await service.get_today_question(user_id=3, today=date(2026, 3, 12))
            await service.submit_answer(
                user_id=3,
                question_id=first.question_id,
                answer_index=0,
                today=date(2026, 3, 12),
            )
            second = await service.get_today_question(user_id=3, today=date(2026, 3, 13))
            await service.submit_answer(
                user_id=3,
                question_id=second.question_id,
                answer_index=1,
                today=date(2026, 3, 13),
            )
            third = await service.get_today_question(user_id=3, today=date(2026, 3, 14))
            answered = await service.submit_answer(
                user_id=3,
                question_id=third.question_id,
                answer_index=2,
                today=date(2026, 3, 14),
            )

            assert answered.current_streak == 3
            assert answered.best_streak == 3
            assert answered.recent_answered_days == 3
            assert any(
                item["badge_key"] == "soul_checkin_3"
                for item in answered.unlocked_badges
            )
    finally:
        await engine.dispose()
