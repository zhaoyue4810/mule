from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_db, get_metadata
from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_admin_ai_task_and_prompt_management() -> None:
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
                "title": "MBTI 16型速测",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 300,
                "sort_order": 1,
                "description": "AI 管理测试版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "report_analysis_v1",
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
                        "question_text": "你更喜欢哪种聚会？",
                        "interaction_type": "bubble",
                        "dim_weights": {"ei": 1},
                        "options": [
                            {
                                "option_code": "a",
                                "seq": 1,
                                "label": "热闹局",
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
                        "keywords": ["轻快", "外放"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "AI 后台用户",
                "duration_seconds": 16,
                "answers": [{"question_seq": 1, "option_code": "a"}],
            },
        )
        assert submit_response.status_code == 200

        task_page_response = client.get("/api/admin/ai/task/page")
        assert task_page_response.status_code == 200
        task_page = task_page_response.json()
        assert task_page["total"] >= 1
        assert task_page["items"][0]["type"] == "report"
        assert task_page["items"][0]["status"] in {"PENDING", "RUNNING", "COMPLETED"}
        assert "duration_ms" in task_page["items"][0]

        overview_response = client.get("/api/admin/ai/task/overview")
        assert overview_response.status_code == 200
        overview = overview_response.json()
        assert overview["total"] >= 1
        assert "providers" in overview

        metrics_response = client.get("/api/admin/ai/task/metrics")
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert metrics["total"] >= 1
        assert "success_rate" in metrics
        assert "failure_rate" in metrics
        assert "avg_duration_ms" in metrics
        assert "tasks_last_24h" in metrics
        assert isinstance(metrics["series"], list)

        metrics_by_week = client.get("/api/admin/ai/task/metrics?bucket=week")
        assert metrics_by_week.status_code == 200
        assert "series" in metrics_by_week.json()

        detail_response = client.get(
            f"/api/admin/ai/task/{task_page['items'][0]['id']}"
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["id"] == task_page["items"][0]["id"]
        assert "provider_errors" in detail
        assert "content" in detail

        prompt_list_response = client.get("/api/admin/ai/prompt/list")
        assert prompt_list_response.status_code == 200
        prompts = prompt_list_response.json()
        assert len(prompts) >= 1
        template = next(item for item in prompts if item["template_code"] == "report_analysis_v1")
        assert template["scene"] == "report"

        update_response = client.put(
            f"/api/admin/ai/prompt/{template['id']}",
            json={
                "system_prompt": template["system_prompt"] + "\n请保持同理心。",
                "user_prompt_tpl": template["user_prompt_tpl"],
                "model_tier": template["model_tier"],
                "temperature": template["temperature"],
                "max_tokens": template["max_tokens"],
                "is_active": template["is_active"],
                "bump_version": True,
            },
        )
        assert update_response.status_code == 200
        updated_template = update_response.json()
        assert updated_template["version"] == template["version"] + 1
        assert "同理心" in updated_template["system_prompt"]

        history_response = client.get(f"/api/admin/ai/prompt/{template['id']}/history")
        assert history_response.status_code == 200
        history_payload = history_response.json()
        assert len(history_payload) >= 2
        assert history_payload[0]["template_id"] == template["id"]

        compare_response = client.get(f"/api/admin/ai/prompt/{template['id']}/compare")
        assert compare_response.status_code == 200
        compare_payload = compare_response.json()
        assert compare_payload["template_id"] == template["id"]
        assert "同理心" in compare_payload["system_prompt_after"]

        retry_task_response = client.post(
            f"/api/admin/ai/task/{task_page['items'][0]['id']}/retry"
        )
        assert retry_task_response.status_code == 200
        assert retry_task_response.json()["retried"] == 1

        retry_failed_response = client.post("/api/admin/ai/task/retry-failed")
        assert retry_failed_response.status_code == 200
        assert "retried" in retry_failed_response.json()
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


async def _prepare_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)
