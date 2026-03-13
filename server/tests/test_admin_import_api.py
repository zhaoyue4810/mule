from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_db, get_metadata
from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_admin_import_task_flow() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        import asyncio

        asyncio.run(_prepare_db(engine))
        client = TestClient(app)
        create_response = client.post(
            "/api/admin/import/tasks",
            json={
                "file_type": "html",
                "file_path": str(REPO_ROOT / "index.html"),
                "operator_id": 1,
            },
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        parse_response = client.post(
            f"/api/admin/import/tasks/{task_id}/parse",
            json={"force": True},
        )
        assert parse_response.status_code == 200
        payload = parse_response.json()
        assert payload["status"] == "DRAFT_READY"
        assert payload["preview_json"]["summary"]["test_count"] == 8
        assert payload["preview_json"]["draft"]["kind"] == "test_catalog"
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_admin_import_apply_flow() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        import asyncio

        asyncio.run(_prepare_db(engine))
        client = TestClient(app)

        create_response = client.post(
            "/api/admin/import/tasks",
            json={
                "file_type": "html",
                "file_path": str(REPO_ROOT / "index.html"),
            },
        )
        task_id = create_response.json()["id"]

        client.post(f"/api/admin/import/tasks/{task_id}/parse", json={"force": True})

        apply_response = client.post(
            f"/api/admin/import/tasks/{task_id}/apply",
            json={"note": "apply import"},
        )
        assert apply_response.status_code == 200
        payload = apply_response.json()
        assert payload["status"] == "APPLIED"
        assert payload["preview_json"]["apply_result"]["created_versions"] == 8
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_admin_content_publish_flow() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        import asyncio

        asyncio.run(_prepare_db(engine))
        client = TestClient(app)

        task_id = client.post(
            "/api/admin/import/tasks",
            json={"file_type": "html", "file_path": str(REPO_ROOT / "index.html")},
        ).json()["id"]
        client.post(f"/api/admin/import/tasks/{task_id}/parse", json={"force": True})
        client.post(f"/api/admin/import/tasks/{task_id}/apply", json={"note": "apply"})

        tests_response = client.get("/api/admin/content/tests")
        assert tests_response.status_code == 200
        assert len(tests_response.json()) == 8

        versions_response = client.get("/api/admin/content/tests/mbti/versions")
        assert versions_response.status_code == 200
        versions = versions_response.json()
        assert versions[0]["status"] == "IMPORTED_DRAFT"
        version_id = versions[0]["id"]

        detail_response = client.get("/api/admin/content/tests/mbti")
        assert detail_response.status_code == 200
        assert detail_response.json()["published_version"] is None

        content_response = client.get(
            f"/api/admin/content/tests/mbti/versions/{version_id}/content"
        )
        assert content_response.status_code == 200
        assert content_response.json()["questions"] == []

        update_response = client.put(
            f"/api/admin/content/tests/mbti/versions/{version_id}/content",
            json={
                "title": "MBTI 16型速测",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 500,
                "sort_order": 1,
                "description": "内容团队编辑稿",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_editorial_v1",
                "dimensions": [
                    {
                        "dim_code": "ei",
                        "dim_name": "外倾-内倾",
                        "max_score": 100,
                        "sort_order": 1,
                    }
                ],
                "questions": [
                    {
                        "question_code": "q1",
                        "seq": 1,
                        "question_text": "你更期待哪种聚会？",
                        "interaction_type": "bubble",
                        "dim_weights": {"ei": 1},
                        "options": [
                            {
                                "option_code": "a",
                                "seq": 1,
                                "label": "热闹社交局",
                                "value": 2,
                                "score_rules": {"dimension_code": "ei", "value": 2},
                            }
                        ],
                    }
                ],
                "personas": [
                    {
                        "persona_key": "entp",
                        "persona_name": "脑洞探索家",
                        "keywords": ["轻快"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["questions"][0]["question_text"] == "你更期待哪种聚会？"

        version_detail_response = client.get(
            f"/api/admin/content/tests/mbti/versions/{version_id}"
        )
        assert version_detail_response.status_code == 200
        assert version_detail_response.json()["question_count"] == 1
        assert version_detail_response.json()["is_published"] is False

        publish_response = client.post(
            "/api/admin/content/tests/mbti/publish",
            json={"version": 1},
        )
        assert publish_response.status_code == 200
        assert publish_response.json()["status"] == "PUBLISHED"

        detail_response = client.get("/api/admin/content/tests/mbti")
        assert detail_response.status_code == 200
        assert detail_response.json()["published_version"] == 1

        version_detail_response = client.get(
            f"/api/admin/content/tests/mbti/versions/{version_id}"
        )
        assert version_detail_response.status_code == 200
        assert version_detail_response.json()["is_published"] is True
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


async def _prepare_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)
