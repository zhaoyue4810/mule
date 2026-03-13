import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_metadata
from app.core.yaml_loader import yaml_config
from app.models import test as test_models
from app.models.test import Option as OptionOrm
from app.models.test import Question as QuestionOrm
from app.models.test import TestVersion as VersionOrm
from app.services.badge_unlock_service import BadgeUnlockService
from app.services.test_submission_service import (
    TestSubmissionService as SubmissionService,
)
from app.services.yaml_sync_service import YamlSyncService
from app.schemas.app_content import (
    TestSubmitAnswerPayload as AnswerPayload,
    TestSubmitRequest as SubmitPayload,
)


def test_first_test_badge_unlock_after_submit() -> None:
    asyncio.run(_test_first_test_badge_unlock_after_submit())


async def _test_first_test_badge_unlock_after_submit() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        yaml_config.load_all()
        async with session_factory() as session:
            sync_service = YamlSyncService(session)
            await sync_service.sync_dictionaries()
            test = test_models.Test(
                test_code="badge_case",
                title="Badge Case",
                category="personality",
                is_match_enabled=False,
            )
            session.add(test)
            await session.flush()

            version = VersionOrm(
                test_id=test.id,
                version=1,
                status="PUBLISHED",
            )
            session.add(version)
            await session.flush()

            question = QuestionOrm(
                version_id=version.id,
                question_code="q1",
                seq=1,
                question_text="Pick one",
                interaction_type="bubble",
                dim_weights={"core": 1},
            )
            session.add(question)
            await session.flush()

            option = OptionOrm(
                question_id=question.id,
                option_code="a",
                seq=1,
                label="A",
                value=1.0,
                score_rules={"dimension_code": "core", "value": 1},
            )
            session.add(option)
            await session.commit()

            submit_service = SubmissionService(session)
            result = await submit_service.submit(
                "badge_case",
                SubmitPayload(
                    nickname="badge-test",
                    duration_seconds=20,
                    answers=[AnswerPayload(question_seq=1, option_code="a")],
                ),
            )
            assert any(
                item["badge_key"] == "first_test" for item in result["unlocked_badges"]
            )
    finally:
        await engine.dispose()


def test_time_range_rule_handles_cross_day_window() -> None:
    service = BadgeUnlockService.__new__(BadgeUnlockService)
    local_tz = ZoneInfo("Asia/Shanghai")
    at_midnight = datetime(2026, 3, 14, 1, 0, tzinfo=local_tz)
    at_noon = datetime(2026, 3, 14, 12, 0, tzinfo=local_tz)

    assert service._rule_matched({"type": "time_range", "start": 23, "end": 5}, 1, at_midnight)
    assert not service._rule_matched({"type": "time_range", "start": 23, "end": 5}, 1, at_noon)
