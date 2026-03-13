import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_metadata
from app.core.yaml_loader import yaml_config
from app.services.soul_fragment_service import SoulFragmentService


def test_unlock_fragment_by_test_code_only_once() -> None:
    asyncio.run(_test_unlock_fragment_by_test_code_only_once())


async def _test_unlock_fragment_by_test_code_only_once() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        yaml_config.load_all()
        async with session_factory() as session:
            service = SoulFragmentService(session)
            first_unlock = await service.unlock_for_user(user_id=1, test_code="love")
            second_unlock = await service.unlock_for_user(user_id=1, test_code="love")
            progress = await service.build_category_progress(1)

            assert len(first_unlock) == 1
            assert first_unlock[0].fragment_key == "emotion_tide"
            assert second_unlock == []
            assert any(
                item["category_code"] == "emotion" and item["unlocked_count"] == 1
                for item in progress
            )
    finally:
        await engine.dispose()


def test_list_user_fragments_returns_unlock_history() -> None:
    asyncio.run(_test_list_user_fragments_returns_unlock_history())


async def _test_list_user_fragments_returns_unlock_history() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        yaml_config.load_all()
        async with session_factory() as session:
            service = SoulFragmentService(session)
            await service.unlock_for_user(user_id=2, test_code="bigfive")
            fragments = await service.list_user_fragments(2)

            assert len(fragments) == 1
            assert fragments[0]["fragment_key"] == "personality_core"
            assert fragments[0]["category"] == "personality"
            assert fragments[0]["unlocked_at"] is not None
    finally:
        await engine.dispose()
