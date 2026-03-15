from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_metadata
from app.models import test as test_models
from app.schemas.admin_content import AdminTestVersionContentUpdateRequest
from app.services.admin_content_service import AdminContentService
from app.services.import_task_service import ImportTaskService
from app.schemas.import_task import ImportTaskCreateRequest


REPO_ROOT = Path(__file__).resolve().parents[2]


async def _build_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


@pytest.mark.anyio
async def test_create_and_parse_html_import_task() -> None:
    engine, session_factory = await _build_session()

    async with session_factory() as session:
        service = ImportTaskService(session)
        task = await service.create_task(
            ImportTaskCreateRequest(
                file_type="html",
                file_path=str(REPO_ROOT / "index.html"),
                operator_id=100,
            )
        )

        assert task.status == "PENDING"

        parsed = await service.parse_task(task.id)

        assert parsed.status == "PREVIEW"
        assert parsed.preview_json is not None
        assert parsed.preview_json["summary"]["test_count"] == 8
        assert parsed.preview_json["draft"]["kind"] == "test_catalog"

    await engine.dispose()


@pytest.mark.anyio
async def test_parse_missing_file_marks_task_failed() -> None:
    engine, session_factory = await _build_session()

    async with session_factory() as session:
        service = ImportTaskService(session)
        task = await service.create_task(
            ImportTaskCreateRequest(
                file_type="html",
                file_path=str(REPO_ROOT / "index.html"),
            )
        )

        task.file_url = str(REPO_ROOT / "missing.html")
        await session.commit()

        parsed = await service.parse_task(task.id, force=True)

        assert parsed.status == "FAILED"
        assert "File missing" in (parsed.parse_log or "")

    await engine.dispose()


@pytest.mark.anyio
async def test_apply_import_task_creates_imported_draft_versions() -> None:
    engine, session_factory = await _build_session()

    async with session_factory() as session:
        service = ImportTaskService(session)
        task = await service.create_task(
            ImportTaskCreateRequest(
                file_type="html",
                file_path=str(REPO_ROOT / "index.html"),
            )
        )
        await service.parse_task(task.id)

        applied = await service.apply_task(task.id, note="applied to content")

        assert applied.status == "APPROVED"
        assert applied.preview_json is not None
        assert applied.preview_json["apply_result"]["applied"] is True
        assert applied.preview_json["apply_result"]["created_versions"] == 8

        test_count = await session.scalar(select(func.count(test_models.Test.id)))
        version_count = await session.scalar(
            select(func.count(test_models.TestVersion.id))
        )
        imported_draft_count = await session.scalar(
            select(func.count(test_models.TestVersion.id)).where(
                test_models.TestVersion.status == "IMPORTED_DRAFT"
            )
        )

        assert test_count == 8
        assert version_count == 8
        assert imported_draft_count == 8

    await engine.dispose()


@pytest.mark.anyio
async def test_imported_draft_can_be_saved_as_structured_content() -> None:
    engine, session_factory = await _build_session()

    async with session_factory() as session:
        import_service = ImportTaskService(session)
        task = await import_service.create_task(
            ImportTaskCreateRequest(
                file_type="html",
                file_path=str(REPO_ROOT / "index.html"),
            )
        )
        await import_service.parse_task(task.id)
        await import_service.apply_task(task.id, note="apply to draft")

        content_service = AdminContentService(session)
        versions = await content_service.list_versions("mbti")
        assert versions
        draft = await content_service.update_version_content(
            "mbti",
            version_id=versions[0].id,
            payload=AdminTestVersionContentUpdateRequest(
                title="MBTI 16型速测",
                category="personality",
                is_match_enabled=False,
                participant_count=120,
                sort_order=1,
                description="导入后的第一版结构化草稿",
                duration_hint="5分钟",
                cover_gradient="sunrise",
                report_template_code="mbti_v1",
                dimensions=[
                    {
                        "dim_code": "ei",
                        "dim_name": "外倾-内倾",
                        "max_score": 100,
                        "sort_order": 1,
                    }
                ],
                questions=[
                    {
                        "question_code": "q1",
                        "seq": 1,
                        "question_text": "周末你更想怎么过？",
                        "interaction_type": "bubble",
                        "dim_weights": {"ei": 1},
                        "options": [
                            {
                                "option_code": "a",
                                "seq": 1,
                                "label": "和朋友出门",
                                "value": 2,
                                "score_rules": {"dimension_code": "ei", "value": 2},
                            },
                            {
                                "option_code": "b",
                                "seq": 2,
                                "label": "自己待着",
                                "value": 1,
                                "score_rules": {"dimension_code": "ei", "value": -2},
                            },
                        ],
                    }
                ],
                personas=[
                    {
                        "persona_key": "entp",
                        "persona_name": "脑洞探索家",
                        "keywords": ["机灵", "跳脱"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            ),
        )

        assert draft["title"] == "MBTI 16型速测"
        assert len(draft["dimensions"]) == 1
        assert len(draft["questions"]) == 1
        assert len(draft["questions"][0]["options"]) == 2
        assert len(draft["personas"]) == 1

    await engine.dispose()


@pytest.mark.anyio
async def test_apply_structured_mock_bundle_creates_full_test_content() -> None:
    engine, session_factory = await _build_session()

    async with session_factory() as session:
        service = ImportTaskService(session)
        task = await service.create_task(
            ImportTaskCreateRequest(
                file_type="html",
                file_path=str(
                    REPO_ROOT / "mock" / "imports" / "xince-full-mock-import.html"
                ),
            )
        )
        await service.parse_task(task.id)
        await service.apply_task(task.id, note="apply mock bundle")

        test = await session.scalar(
            select(test_models.Test).where(test_models.Test.test_code == "mbti")
        )
        assert test is not None
        assert test.participant_count > 0

        version = await session.scalar(
            select(test_models.TestVersion)
            .where(test_models.TestVersion.test_id == test.id)
            .order_by(test_models.TestVersion.version.desc())
        )
        assert version is not None
        assert version.status == "IMPORTED_DRAFT"
        assert version.cover_gradient
        assert version.report_template_code == "mbti_mock_v1"

        question_count = await session.scalar(
            select(func.count(test_models.Question.id)).where(
                test_models.Question.version_id == version.id
            )
        )
        persona_count = await session.scalar(
            select(func.count(test_models.TestPersona.id)).where(
                test_models.TestPersona.version_id == version.id
            )
        )

        assert question_count and question_count > 0
        assert persona_count and persona_count > 0

    await engine.dispose()
