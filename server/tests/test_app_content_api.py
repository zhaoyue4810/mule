from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_db, get_metadata
from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_app_tests_only_return_published_content() -> None:
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
                "description": "用户端已发布版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
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
                        "keywords": ["外放"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        list_response = client.get("/api/app/tests")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert len(payload) == 1
        assert payload[0]["test_code"] == "mbti"
        assert payload[0]["question_count"] == 1

        detail_response = client.get("/api/app/tests/mbti")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["version"] == 1
        assert detail["question_count"] == 1
        assert detail["dimension_count"] == 1
        assert detail["persona_count"] == 1
        assert detail["personas"][0]["persona_key"] == "entp"

        questionnaire_response = client.get("/api/app/tests/mbti/questionnaire")
        assert questionnaire_response.status_code == 200
        questionnaire = questionnaire_response.json()
        assert questionnaire["question_count"] == 1
        assert questionnaire["questions"][0]["interaction_type"] == "bubble"
        assert questionnaire["questions"][0]["options"][0]["label"] == "热闹局"

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "测试访客",
                "duration_seconds": 18,
                "answers": [
                    {
                        "question_seq": 1,
                        "option_code": "a",
                    }
                ],
            },
        )
        assert submit_response.status_code == 200
        submit_payload = submit_response.json()
        assert submit_payload["test_code"] == "mbti"
        assert submit_payload["version"] == 1
        assert submit_payload["answers"][0]["label"] == "热闹局"
        assert submit_payload["persona_key"] == "entp"
        assert submit_payload["record_id"] >= 1
        assert any(
            item["badge_key"] == "first_test"
            for item in submit_payload.get("unlocked_badges", [])
        )
        assert submit_payload.get("unlocked_fragments", []) == []

        report_response = client.get(
            f"/api/app/reports/{submit_payload['record_id']}"
        )
        assert report_response.status_code == 200
        report_payload = report_response.json()
        assert report_payload["test_code"] == "mbti"
        assert report_payload["answered_count"] == 1
        assert report_payload["persona"]["persona_key"] == "entp"
        assert report_payload["top_dimensions"][0]["dim_code"] == "ei"
        assert report_payload["radar_dimensions"][0]["dim_code"] == "ei"
        assert report_payload["persona_tags"]
        assert report_payload["soul_weather"]["title"]
        assert len(report_payload["metaphor_cards"]) == 3
        assert report_payload["dna_segments"][0]["dim_code"] == "ei"
        assert report_payload["action_guides"]
        assert report_payload["result_tier"]
        assert report_payload["ai_status"] in {"PENDING", "COMPLETED"}
        assert report_payload["share_card"]["title"]
        assert report_payload["share_card"]["share_text"]
        assert report_payload["share_card"]["highlight_lines"]
        assert report_payload["share_card"]["theme"]
        assert report_payload["share_card"]["background"]
        assert report_payload["share_card"]["badge"]
        assert report_payload["share_card"]["footer"]
        assert report_payload["share_card"]["stat_chips"]

        ai_status_response = client.get(
            f"/api/app/reports/{submit_payload['record_id']}/ai-status"
        )
        assert ai_status_response.status_code == 200
        ai_status_payload = ai_status_response.json()
        assert ai_status_payload["status"] in {"RUNNING", "COMPLETED", "PENDING"}
        assert ai_status_payload["provider"] == "fallback" or ai_status_payload["provider"] is None

        retry_response = client.post(
            "/api/app/ai/report/retry",
            json={"record_id": submit_payload["record_id"]},
        )
        assert retry_response.status_code == 200
        retry_payload = retry_response.json()
        assert retry_payload["record_id"] == submit_payload["record_id"]
        assert retry_payload["status"] in {"PENDING", "RUNNING", "COMPLETED"}

        profile_overview_response = client.get(
            f"/api/app/profile/{submit_payload['user_id']}/overview"
        )
        assert profile_overview_response.status_code == 200
        profile_overview = profile_overview_response.json()
        assert profile_overview["test_count"] == 1
        assert profile_overview["distinct_test_count"] == 1
        assert profile_overview["recent_reports"][0]["record_id"] == submit_payload["record_id"]
        assert profile_overview["dominant_dimensions"][0]["dim_code"] == "ei"
        assert any(item["badge_key"] == "first_test" for item in profile_overview["badges"])
        assert len(profile_overview["calendar_heatmap"]) == 30
        assert any(item["activity_count"] >= 1 for item in profile_overview["calendar_heatmap"])
        assert profile_overview["soul_fragments"] == []
        assert len(profile_overview["fragment_progress"]) >= 1

        profile_reports_response = client.get(
            f"/api/app/profile/{submit_payload['user_id']}/reports"
        )
        assert profile_reports_response.status_code == 200
        profile_reports = profile_reports_response.json()
        assert len(profile_reports) == 1
        assert profile_reports[0]["record_id"] == submit_payload["record_id"]

        hidden_response = client.get("/api/app/tests/bigfive")
        assert hidden_response.status_code == 404
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


async def _prepare_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)


def test_profile_history_orders_latest_reports_first() -> None:
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
                "description": "用户端已发布版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
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
                            },
                            {
                                "option_code": "b",
                                "seq": 2,
                                "label": "安静局",
                                "value": 1,
                                "score_rules": {"dimension_code": "ei", "value": 1},
                            },
                        ],
                    }
                ],
                "personas": [
                    {
                        "persona_key": "entp",
                        "persona_name": "脑洞探索家",
                        "keywords": ["外放"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        guest_response = client.post(
            "/api/app/auth/guest",
            json={"nickname": "连续测试用户"},
        )
        guest_payload = guest_response.json()
        headers = {"Authorization": f"Bearer {guest_payload['access_token']}"}

        first_submit = client.post(
            "/api/app/tests/mbti/submit",
            headers=headers,
            json={
                "duration_seconds": 12,
                "answers": [{"question_seq": 1, "option_code": "a"}],
            },
        ).json()
        second_submit_response = client.post(
            "/api/app/tests/mbti/submit",
            headers=headers,
            json={
                "duration_seconds": 30,
                "answers": [{"question_seq": 1, "option_code": "b"}],
            },
        )
        assert second_submit_response.status_code == 200
        second_submit = second_submit_response.json()

        profile_overview_response = client.get(
            f"/api/app/profile/{first_submit['user_id']}/overview"
        )
        assert profile_overview_response.status_code == 200
        profile_overview = profile_overview_response.json()
        assert profile_overview["test_count"] == 2
        assert profile_overview["distinct_test_count"] == 1
        assert profile_overview["avg_duration_seconds"] == 21
        assert profile_overview["recent_reports"][0]["record_id"] == second_submit["record_id"]
        assert profile_overview["recent_reports"][1]["record_id"] == first_submit["record_id"]
        assert profile_overview["persona_distribution"][0]["persona_key"] == "entp"

        profile_reports_response = client.get(
            f"/api/app/profile/{first_submit['user_id']}/reports"
        )
        assert profile_reports_response.status_code == 200
        profile_reports = profile_reports_response.json()
        assert len(profile_reports) == 2
        assert profile_reports[0]["record_id"] == second_submit["record_id"]
        assert profile_reports[1]["record_id"] == first_submit["record_id"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_unlocks_soul_fragment_when_test_matches_definition() -> None:
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

        versions = client.get("/api/admin/content/tests/love/versions").json()
        version_id = versions[0]["id"]
        client.put(
            f"/api/admin/content/tests/love/versions/{version_id}/content",
            json={
                "title": "恋爱能量速测",
                "category": "emotion",
                "is_match_enabled": False,
                "participant_count": 180,
                "sort_order": 2,
                "description": "灵魂碎片测试用例",
                "duration_hint": "3分钟",
                "cover_gradient": "sunset",
                "report_template_code": "love_public_v1",
                "dimensions": [
                    {
                        "dim_code": "heart",
                        "dim_name": "心动值",
                        "max_score": 100,
                        "sort_order": 1,
                    }
                ],
                "questions": [
                    {
                        "question_code": "q1",
                        "seq": 1,
                        "question_text": "今天你更想如何靠近喜欢的人？",
                        "interaction_type": "bubble",
                        "dim_weights": {"heart": 1},
                        "options": [
                            {
                                "option_code": "a",
                                "seq": 1,
                                "label": "直接表达",
                                "value": 3,
                                "score_rules": {"dimension_code": "heart", "value": 3},
                            }
                        ],
                    }
                ],
                "personas": [
                    {
                        "persona_key": "warm",
                        "persona_name": "心动表达者",
                        "keywords": ["热烈"],
                        "dim_pattern": {"heart": "H"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/love/publish", json={"version": 1})

        submit_response = client.post(
            "/api/app/tests/love/submit",
            json={
                "nickname": "碎片用户",
                "duration_seconds": 16,
                "answers": [{"question_seq": 1, "option_code": "a"}],
            },
        )
        assert submit_response.status_code == 200
        submit_payload = submit_response.json()
        assert any(
            item["fragment_key"] == "emotion_tide"
            for item in submit_payload["unlocked_fragments"]
        )

        profile_overview_response = client.get(
            f"/api/app/profile/{submit_payload['user_id']}/overview"
        )
        assert profile_overview_response.status_code == 200
        profile_overview = profile_overview_response.json()
        assert any(
            item["fragment_key"] == "emotion_tide"
            for item in profile_overview["soul_fragments"]
        )
        assert any(
            item["category_code"] == "emotion" and item["unlocked_count"] >= 1
            for item in profile_overview["fragment_progress"]
        )
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_requires_complete_answer_set() -> None:
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
                "description": "用户端已发布版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
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
                    },
                    {
                        "question_code": "q2",
                        "seq": 2,
                        "question_text": "你会主动发起聊天吗？",
                        "interaction_type": "swipe",
                        "dim_weights": {"ei": 1},
                        "options": [],
                    },
                ],
                "personas": [
                    {
                        "persona_key": "entp",
                        "persona_name": "脑洞探索家",
                        "keywords": ["外放"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "测试访客",
                "duration_seconds": 18,
                "answers": [{"question_seq": 1, "option_code": "a"}],
            },
        )
        assert submit_response.status_code == 409
        assert "Missing answers" in submit_response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_rejects_wrong_answer_shape_for_interaction_type() -> None:
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
                "description": "用户端已发布版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
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
                    },
                    {
                        "question_code": "q2",
                        "seq": 2,
                        "question_text": "你会主动发起聊天吗？",
                        "interaction_type": "slider",
                        "config": {"min": 1, "max": 5},
                        "dim_weights": {"ei": 1},
                        "options": [],
                    },
                ],
                "personas": [
                    {
                        "persona_key": "entp",
                        "persona_name": "脑洞探索家",
                        "keywords": ["外放"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        wrong_numeric_shape = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "测试访客",
                "duration_seconds": 18,
                "answers": [
                    {"question_seq": 1, "numeric_value": 1},
                    {"question_seq": 2, "numeric_value": 3},
                ],
            },
        )
        assert wrong_numeric_shape.status_code == 409
        assert "requires option_code" in wrong_numeric_shape.json()["detail"]

        wrong_option_shape = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "测试访客",
                "duration_seconds": 18,
                "answers": [
                    {"question_seq": 1, "option_code": "a"},
                    {"question_seq": 2, "option_code": "a"},
                ],
            },
        )
        assert wrong_option_shape.status_code == 409
        assert "requires numeric_value" in wrong_option_shape.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_rejects_out_of_range_numeric_value() -> None:
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
                "description": "用户端已发布版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
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
                        "question_text": "你会主动发起聊天吗？",
                        "interaction_type": "slider",
                        "config": {"min": 1, "max": 5},
                        "dim_weights": {"ei": 1},
                        "options": [],
                    }
                ],
                "personas": [
                    {
                        "persona_key": "entp",
                        "persona_name": "脑洞探索家",
                        "keywords": ["外放"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "测试访客",
                "duration_seconds": 18,
                "answers": [{"question_seq": 1, "numeric_value": 9}],
            },
        )
        assert submit_response.status_code == 409
        assert "requires value between" in submit_response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_supports_rank_and_plot2d_answers() -> None:
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
                "title": "MBTI 复杂题型版",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 300,
                "sort_order": 1,
                "description": "用户端已发布版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
                "dimensions": [
                    {
                        "dim_code": "logic",
                        "dim_name": "理性",
                        "max_score": 100,
                        "sort_order": 1,
                    },
                    {
                        "dim_code": "social",
                        "dim_name": "社交",
                        "max_score": 100,
                        "sort_order": 2,
                    },
                ],
                "questions": [
                    {
                        "question_code": "q1",
                        "seq": 1,
                        "question_text": "请给以下特质排序",
                        "interaction_type": "rank",
                        "dim_weights": {"logic": 1},
                        "options": [
                            {
                                "option_code": "a",
                                "seq": 1,
                                "label": "分析",
                                "value": 1.0,
                            },
                            {
                                "option_code": "b",
                                "seq": 2,
                                "label": "表达",
                                "value": 0.8,
                            },
                            {
                                "option_code": "c",
                                "seq": 3,
                                "label": "协调",
                                "value": 0.6,
                            },
                        ],
                    },
                    {
                        "question_code": "q2",
                        "seq": 2,
                        "question_text": "在二维坐标中选一个位置",
                        "interaction_type": "plot2d",
                        "config": {
                            "x_min": "内向",
                            "x_max": "外向",
                            "y_min": "感性",
                            "y_max": "理性",
                        },
                        "dim_weights": {"social": 1, "logic": 1},
                        "options": [],
                    },
                ],
                "personas": [
                    {
                        "persona_key": "strategist",
                        "persona_name": "策略观察者",
                        "keywords": ["理性"],
                        "dim_pattern": {"logic": "H"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "复杂题型用户",
                "duration_seconds": 25,
                "answers": [
                    {
                        "question_seq": 1,
                        "ordered_option_codes": ["a", "b", "c"],
                    },
                    {
                        "question_seq": 2,
                        "point": {"x": 0.8, "y": 0.6},
                    },
                ],
            },
        )
        assert submit_response.status_code == 200
        payload = submit_response.json()
        assert payload["record_id"] >= 1
        assert payload["answers"][0]["label"] == "分析 > 表达 > 协调"
        assert "坐标" in payload["answers"][1]["label"]

        report_response = client.get(f"/api/app/reports/{payload['record_id']}")
        assert report_response.status_code == 200
        report_payload = report_response.json()
        assert "logic" in report_payload["dimension_scores"]
        assert "social" in report_payload["dimension_scores"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_supports_colorpick_numeric_answer() -> None:
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
                "title": "MBTI 色彩题型版",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 300,
                "sort_order": 1,
                "description": "用户端已发布版本",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
                "dimensions": [
                    {
                        "dim_code": "mood",
                        "dim_name": "情绪",
                        "max_score": 100,
                        "sort_order": 1,
                    }
                ],
                "questions": [
                    {
                        "question_code": "q1",
                        "seq": 1,
                        "question_text": "选一个更像你此刻的色相",
                        "interaction_type": "colorpick",
                        "config": {"min_hue": 0, "max_hue": 360},
                        "dim_weights": {"mood": 1},
                        "options": [],
                    }
                ],
                "personas": [
                    {
                        "persona_key": "calm",
                        "persona_name": "平衡观察者",
                        "keywords": ["平和"],
                        "dim_pattern": {"mood": "H"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "色彩用户",
                "duration_seconds": 12,
                "answers": [{"question_seq": 1, "numeric_value": 180}],
            },
        )
        assert submit_response.status_code == 200
        payload = submit_response.json()
        assert payload["record_id"] >= 1
        assert payload["answers"][0]["label"] == "数值 180.0"
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_rejects_non_integer_discrete_numeric_answers() -> None:
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
                "title": "MBTI 离散数值校验版",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 300,
                "sort_order": 1,
                "description": "离散数值题型校验",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
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
                        "question_text": "你会给今天的社交状态打几星？",
                        "interaction_type": "star",
                        "config": {"min": 1, "max_stars": 5},
                        "dim_weights": {"ei": 1},
                        "options": [],
                    }
                ],
                "personas": [],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "离散数值用户",
                "duration_seconds": 16,
                "answers": [{"question_seq": 1, "numeric_value": 3.5}],
            },
        )
        assert submit_response.status_code == 409
        assert "requires integer steps" in submit_response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_rejects_invalid_plot2d_point() -> None:
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
                "title": "MBTI 坐标题型校验版",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 300,
                "sort_order": 1,
                "description": "plot2d 边界校验",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
                "dimensions": [
                    {
                        "dim_code": "logic",
                        "dim_name": "理性",
                        "max_score": 100,
                        "sort_order": 1,
                    },
                    {
                        "dim_code": "social",
                        "dim_name": "社交",
                        "max_score": 100,
                        "sort_order": 2,
                    },
                ],
                "questions": [
                    {
                        "question_code": "q1",
                        "seq": 1,
                        "question_text": "在二维坐标中选一个位置",
                        "interaction_type": "plot2d",
                        "config": {
                            "x_min": "内向",
                            "x_max": "外向",
                            "y_min": "感性",
                            "y_max": "理性",
                        },
                        "dim_weights": {"social": 1, "logic": 1},
                        "options": [],
                    }
                ],
                "personas": [],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "nickname": "坐标用户",
                "duration_seconds": 22,
                "answers": [{"question_seq": 1, "point": {"x": 1.2, "y": 0.6}}],
            },
        )
        assert submit_response.status_code == 409
        assert "requires x and y between 0 and 1" in submit_response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_rejects_explicit_user_id_without_auth() -> None:
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
                "title": "MBTI 显式用户提交校验版",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 300,
                "sort_order": 1,
                "description": "显式 user_id 需要鉴权",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
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
                            }
                        ],
                    }
                ],
                "personas": [],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        guest_response = client.post("/api/app/auth/guest", json={"nickname": "访客A"})
        guest_payload = guest_response.json()

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "user_id": guest_payload["user"]["user_id"],
                "duration_seconds": 10,
                "answers": [{"question_seq": 1, "option_code": "a"}],
            },
        )
        assert submit_response.status_code == 401
        assert "Authorization required" in submit_response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_submit_rejects_mismatched_user_id_for_current_session() -> None:
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
                "title": "MBTI 会话用户校验版",
                "category": "personality",
                "is_match_enabled": False,
                "participant_count": 300,
                "sort_order": 1,
                "description": "token 用户和 payload.user_id 必须一致",
                "duration_hint": "5分钟",
                "cover_gradient": "dawn",
                "report_template_code": "mbti_public_v1",
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
                            }
                        ],
                    }
                ],
                "personas": [],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        guest_a = client.post("/api/app/auth/guest", json={"nickname": "访客A"}).json()
        guest_b = client.post("/api/app/auth/guest", json={"nickname": "访客B"}).json()
        headers = {"Authorization": f"Bearer {guest_a['access_token']}"}

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            headers=headers,
            json={
                "user_id": guest_b["user"]["user_id"],
                "duration_seconds": 10,
                "answers": [{"question_seq": 1, "option_code": "a"}],
            },
        )
        assert submit_response.status_code == 403
        assert "does not match current session" in submit_response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())
