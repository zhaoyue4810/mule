import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_metadata
from app.models.ai import AiAnalysis, AiPromptTemplate
from app.models.record import TestRecord as RecordOrm
from app.models.report import ReportSnapshot
from app.models.test import Test as OrmTest
from app.models.test import TestVersion as VersionOrm
from app.models.user import User
from app.services.prompt_template_service import PromptTemplateService
from app.services.report_ai_service import (
    AI_STATUS_COMPLETED,
    ReportAiService,
)


def test_prompt_template_defaults_can_sync() -> None:
    asyncio.run(_test_prompt_template_defaults_can_sync())


async def _test_prompt_template_defaults_can_sync() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        async with session_factory() as session:
            service = PromptTemplateService(session)
            await service.ensure_defaults()

            template = await session.scalar(
                select(AiPromptTemplate).where(
                    AiPromptTemplate.template_code == "report_analysis_v1"
                )
            )
            assert template is not None
            assert template.scene == "report"
            assert template.max_tokens == 800
    finally:
        await engine.dispose()


def test_report_ai_job_uses_prompt_template_fallback() -> None:
    asyncio.run(_test_report_ai_job_uses_prompt_template_fallback())


async def _test_report_ai_job_uses_prompt_template_fallback() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(get_metadata().create_all)

        async with session_factory() as session:
            user = User(nickname="AI 用户", avatar_value="🧠", onboarding_completed=False)
            session.add(user)
            await session.flush()

            test = OrmTest(
                test_code="mbti",
                title="MBTI 16型速测",
                category="personality",
            )
            session.add(test)
            await session.flush()

            version = VersionOrm(
                test_id=test.id,
                version=1,
                status="PUBLISHED",
                report_template_code="report_analysis_v1",
            )
            session.add(version)
            await session.flush()

            record = RecordOrm(
                user_id=user.id,
                test_id=test.id,
                version_id=version.id,
                scores={"ei": 2.0},
                total_score=8,
                duration=21,
            )
            session.add(record)
            await session.flush()

            snapshot = ReportSnapshot(
                record_id=record.id,
                dimension_scores={"ei": 2.0},
                overall_score=8,
                persona_code=None,
                report_json={
                    "persona_name": "脑洞探索家",
                    "summary": "你更偏向外放表达。",
                    "top_dimensions": [{"dim_code": "ei", "score": 2.0}],
                },
                ai_text=None,
            )
            session.add(snapshot)
            await session.flush()

            ai_service = ReportAiService(session)
            await ai_service.enqueue_report_analysis(record.id)

        await ReportAiService.run_report_analysis_job(session_factory, record.id)

        async with session_factory() as session:
            analysis = await session.scalar(
                select(AiAnalysis).where(
                    AiAnalysis.type == "report",
                    AiAnalysis.ref_id == record.id,
                )
            )
            snapshot = await session.scalar(
                select(ReportSnapshot).where(ReportSnapshot.record_id == record.id)
            )

            assert analysis is not None
            assert analysis.status == AI_STATUS_COMPLETED
            assert analysis.provider == "fallback"
            assert analysis.started_at is not None
            assert analysis.completed_at is not None
            assert analysis.provider_errors == []
            assert analysis.error_message is None
            assert snapshot is not None
            assert snapshot.ai_text
            assert "MBTI 16型速测" in snapshot.ai_text
    finally:
        await engine.dispose()
