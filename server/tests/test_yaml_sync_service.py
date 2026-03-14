import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_metadata
from app.core.yaml_loader import yaml_config
from app.models import test as test_models
from app.models.badge import BadgeDefinition
from app.models.calendar import DailySoulQuestion
from app.models.soul import SoulFragmentDefinition
from app.services.yaml_sync_service import YamlSyncService


async def _build_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


@pytest.mark.anyio
async def test_sync_single_test_creates_runtime_entities() -> None:
    yaml_config.load_all()
    engine, session_factory = await _build_session()

    async with session_factory() as session:
        service = YamlSyncService(session)
        result = await service.sync_test("mbti")

        assert result.test_code == "mbti"
        assert result.created_version == 1

        test_count = await session.scalar(select(func.count(test_models.Test.id)))
        version_count = await session.scalar(
            select(func.count(test_models.TestVersion.id))
        )
        question_count = await session.scalar(
            select(func.count(test_models.Question.id))
        )
        option_count = await session.scalar(select(func.count(test_models.Option.id)))
        dimension_count = await session.scalar(
            select(func.count(test_models.Dimension.id))
        )
        persona_count = await session.scalar(
            select(func.count(test_models.TestPersona.id))
        )

        assert test_count == 1
        assert version_count == 1
        assert question_count == 4
        assert option_count == 6
        assert dimension_count == 4
        assert persona_count == 2

    await engine.dispose()


@pytest.mark.anyio
async def test_sync_all_tests_creates_eight_tests() -> None:
    yaml_config.load_all()
    engine, session_factory = await _build_session()

    async with session_factory() as session:
        service = YamlSyncService(session)
        results = await service.sync_all_tests()

        assert len(results) == 8
        test_count = await session.scalar(select(func.count(test_models.Test.id)))
        version_count = await session.scalar(
            select(func.count(test_models.TestVersion.id))
        )

        assert test_count == 8
        assert version_count == 8

    await engine.dispose()


@pytest.mark.anyio
async def test_sync_dictionaries_creates_runtime_dictionary_rows() -> None:
    yaml_config.load_all()
    engine, session_factory = await _build_session()

    async with session_factory() as session:
        service = YamlSyncService(session)
        summary = await service.sync_dictionaries()

        assert summary.badge_count == 5
        assert summary.daily_question_count == 3
        assert summary.soul_fragment_count == 5

        badge_count = await session.scalar(select(func.count(BadgeDefinition.id)))
        daily_question_count = await session.scalar(
            select(func.count(DailySoulQuestion.id))
        )
        soul_fragment_count = await session.scalar(
            select(func.count(SoulFragmentDefinition.id))
        )

        assert badge_count == 5
        assert daily_question_count == 3
        assert soul_fragment_count == 5

    await engine.dispose()
