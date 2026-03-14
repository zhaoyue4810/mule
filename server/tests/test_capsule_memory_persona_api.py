from datetime import datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_db, get_metadata
from app.main import app
from app.models.soul import TimeCapsule


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_capsule_memory_and_persona_card_flow() -> None:
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

        versions = client.get("/api/admin/content/tests/mbti/versions").json()
        version_id = versions[0]["id"]
        client.put(
            f"/api/admin/content/tests/mbti/versions/{version_id}/content",
            json={
                "title": "MBTI 记忆链路版",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 300,
                "sort_order": 1,
                "description": "P2 能力测试版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "report_analysis_v1",
                "dimensions": [
                    {
                        "dim_code": "ei",
                        "dim_name": "外倾-内倾",
                        "max_score": 100,
                        "sort_order": 1,
                    },
                    {
                        "dim_code": "sn",
                        "dim_name": "感觉-直觉",
                        "max_score": 100,
                        "sort_order": 2,
                    },
                ],
                "questions": [
                    {
                        "question_code": "q1",
                        "seq": 1,
                        "question_text": "你更喜欢哪种聚会？",
                        "interaction_type": "bubble",
                        "dim_weights": {"ei": 1},
                        "options": [
                            {
                                "option_code": "a",
                                "seq": 1,
                                "label": "热闹局",
                                "value": 88,
                                "score_rules": {"dimension_code": "ei", "value": 88},
                            }
                        ],
                    },
                    {
                        "question_code": "q2",
                        "seq": 2,
                        "question_text": "你更相信什么？",
                        "interaction_type": "bubble",
                        "dim_weights": {"sn": 1},
                        "options": [
                            {
                                "option_code": "a",
                                "seq": 1,
                                "label": "直觉感受",
                                "value": 82,
                                "score_rules": {"dimension_code": "sn", "value": 82},
                            }
                        ],
                    },
                ],
                "personas": [
                    {
                        "persona_key": "entp",
                        "persona_name": "脑洞探索家",
                        "emoji": "🪐",
                        "keywords": ["外放", "好奇", "灵感"],
                        "soul_signature": "你把灵感当作和世界打招呼的方式。",
                        "dim_pattern": {"ei": "E", "sn": "N"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        auth_response = client.post("/api/app/auth/guest", json={"nickname": "胶囊用户"})
        headers = {"Authorization": f"Bearer {auth_response.json()['access_token']}"}

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            headers=headers,
            json={
                "duration_seconds": 18,
                "answers": [
                    {"question_seq": 1, "option_code": "a"},
                    {"question_seq": 2, "option_code": "a"},
                ],
            },
        )
        assert submit_response.status_code == 200
        record_id = submit_response.json()["record_id"]

        report_response = client.get(f"/api/app/reports/{record_id}", headers=headers)
        assert report_response.status_code == 200
        report_payload = report_response.json()
        assert report_payload["report_id"] >= 1

        greeting_response = client.get("/api/app/memory/greeting", headers=headers)
        assert greeting_response.status_code == 200
        greeting_payload = greeting_response.json()
        assert greeting_payload["know_level"] == 1
        assert greeting_payload["test_count"] == 1

        suggest_response = client.get("/api/app/memory/suggest", headers=headers)
        assert suggest_response.status_code == 200
        assert "items" in suggest_response.json()

        persona_response = client.get("/api/app/profile/persona-card", headers=headers)
        assert persona_response.status_code == 200
        persona_payload = persona_response.json()
        assert persona_payload["persona_title"] == "脑洞探索家"
        assert persona_payload["dimensions"]
        assert persona_payload["weather"]["emoji"]

        create_capsule_response = client.post(
            "/api/app/capsule/create",
            headers=headers,
            json={
                "message": "希望未来的我，依然记得今天的勇气。",
                "duration_days": 30,
                "report_id": report_payload["report_id"],
            },
        )
        assert create_capsule_response.status_code == 200
        capsule_payload = create_capsule_response.json()
        assert capsule_payload["duration_days"] == 30
        assert capsule_payload["persona_title"] == "脑洞探索家"

        list_response = client.get("/api/app/capsule/list", headers=headers)
        assert list_response.status_code == 200
        list_payload = list_response.json()
        assert len(list_payload["items"]) == 1
        assert list_payload["items"][0]["days_remaining"] >= 29

        check_response = client.get("/api/app/capsule/check", headers=headers)
        assert check_response.status_code == 200
        assert check_response.json()["has_revealable"] is False

        async def unlock_capsule():
            async with session_factory() as session:
                item = await session.scalar(select(TimeCapsule).where(TimeCapsule.id == capsule_payload["id"]))
                item.unlock_date = datetime.now().date() - timedelta(days=1)
                await session.commit()

        asyncio.run(unlock_capsule())

        check_again = client.get("/api/app/capsule/check", headers=headers)
        assert check_again.status_code == 200
        assert check_again.json()["has_revealable"] is True

        reveal_response = client.post(
            f"/api/app/capsule/{capsule_payload['id']}/reveal",
            headers=headers,
        )
        assert reveal_response.status_code == 200
        assert reveal_response.json()["revealed"] is True

        settings_response = client.put(
            "/api/app/profile/me/settings",
            headers=headers,
            json={"sound_enabled": False},
        )
        assert settings_response.status_code == 200
        assert settings_response.json()["sound_enabled"] is False
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


async def _prepare_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)
