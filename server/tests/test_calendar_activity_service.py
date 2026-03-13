import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_metadata
from app.models.calendar import CalendarEntry
from app.services.calendar_activity_service import CalendarActivityService


def test_calendar_heatmap_groups_activity_counts() -> None:
    asyncio.run(_test_calendar_heatmap_groups_activity_counts())


async def _test_calendar_heatmap_groups_activity_counts() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        async with session_factory() as session:
            session.add_all(
                [
                    CalendarEntry(
                        user_id=1,
                        date=date(2026, 3, 12),
                        mood_level=None,
                        test_record_id=101,
                        source="test",
                    ),
                    CalendarEntry(
                        user_id=1,
                        date=date(2026, 3, 12),
                        mood_level=None,
                        test_record_id=102,
                        source="test",
                    ),
                    CalendarEntry(
                        user_id=1,
                        date=date(2026, 3, 14),
                        mood_level=None,
                        test_record_id=103,
                        source="test",
                    ),
                ]
            )
            await session.commit()

            service = CalendarActivityService(session)
            items = await service.build_heatmap(
                user_id=1,
                days=4,
                end_date=date(2026, 3, 14),
            )

            assert [item.date for item in items] == [
                "2026-03-11",
                "2026-03-12",
                "2026-03-13",
                "2026-03-14",
            ]
            assert items[1].activity_count == 2
            assert items[1].intensity == 2
            assert items[3].activity_count == 1
            assert items[3].intensity == 1
    finally:
        await engine.dispose()


def test_record_test_completion_uses_local_date() -> None:
    asyncio.run(_test_record_test_completion_uses_local_date())


async def _test_record_test_completion_uses_local_date() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        async with session_factory() as session:
            service = CalendarActivityService(session)
            await service.record_test_completion(
                user_id=7,
                test_record_id=88,
                completed_at=datetime(2026, 3, 14, 0, 30, tzinfo=ZoneInfo("Asia/Shanghai")),
            )
            await session.commit()

            item = await session.get(CalendarEntry, 1)
            assert item is not None
            assert item.date.isoformat() == "2026-03-14"
            assert item.source == "test"
    finally:
        await engine.dispose()
