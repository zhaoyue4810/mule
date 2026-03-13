from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_db, get_metadata
from app.main import app
from app.models.record import TestRecord as RecordOrm
from app.models.user import User


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_guest_auth_and_profile_me_flow() -> None:
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
                "description": "认证链路测试版本",
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
                        "keywords": ["外放"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        auth_response = client.post(
            "/api/app/auth/guest",
            json={"nickname": "H5 访客"},
        )
        assert auth_response.status_code == 200
        auth_payload = auth_response.json()
        assert auth_payload["access_token"]
        assert auth_payload["user"]["is_guest"] is True

        headers = {"Authorization": f"Bearer {auth_payload['access_token']}"}

        me_response = client.get("/api/app/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_payload = me_response.json()
        assert me_payload["user_id"] == auth_payload["user"]["user_id"]
        assert me_payload["nickname"] == "H5 访客"

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "duration_seconds": 12,
                "answers": [{"question_seq": 1, "option_code": "a"}],
            },
            headers=headers,
        )
        assert submit_response.status_code == 200
        submit_payload = submit_response.json()
        assert submit_payload["user_id"] == auth_payload["user"]["user_id"]

        overview_response = client.get("/api/app/profile/me/overview", headers=headers)
        assert overview_response.status_code == 200
        overview_payload = overview_response.json()
        assert overview_payload["user_id"] == auth_payload["user"]["user_id"]
        assert overview_payload["test_count"] == 1

        reports_response = client.get("/api/app/profile/me/reports", headers=headers)
        assert reports_response.status_code == 200
        reports_payload = reports_response.json()
        assert len(reports_payload) == 1
        assert reports_payload[0]["record_id"] == submit_payload["record_id"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_wechat_mini_program_login_returns_placeholder_when_not_configured() -> None:
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
        response = client.post(
            "/api/app/auth/wechat/mini-program",
            json={"code": "temporary-code"},
        )
        assert response.status_code == 503
        assert "credentials are not configured" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_phone_login_can_create_session_from_verification_code() -> None:
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

        send_response = client.post(
            "/api/app/auth/phone/send-code",
            json={"phone": "13800138000"},
        )
        assert send_response.status_code == 200
        send_payload = send_response.json()
        assert send_payload["provider"] == "mock"
        assert send_payload["debug_code"]

        login_response = client.post(
            "/api/app/auth/phone-login",
            json={
                "phone": "13800138000",
                "code": send_payload["debug_code"],
            },
        )
        assert login_response.status_code == 200
        login_payload = login_response.json()
        assert login_payload["user"]["has_phone"] is True
        assert login_payload["user"]["is_guest"] is False
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_guest_phone_bind_keeps_existing_records() -> None:
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
                "description": "认证链路测试版本",
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
                        "keywords": ["外放"],
                        "dim_pattern": {"ei": "E"},
                    }
                ],
            },
        )
        client.post("/api/admin/content/tests/mbti/publish", json={"version": 1})

        guest_response = client.post("/api/app/auth/guest", json={"nickname": "临时访客"})
        guest_payload = guest_response.json()
        headers = {"Authorization": f"Bearer {guest_payload['access_token']}"}

        submit_response = client.post(
            "/api/app/tests/mbti/submit",
            json={
                "duration_seconds": 9,
                "answers": [{"question_seq": 1, "option_code": "a"}],
            },
            headers=headers,
        )
        assert submit_response.status_code == 200
        record_id = submit_response.json()["record_id"]

        send_response = client.post(
            "/api/app/auth/phone/send-code",
            json={"phone": "13900139000"},
        )
        bind_response = client.post(
            "/api/app/auth/phone/bind",
            json={
                "phone": "13900139000",
                "code": send_response.json()["debug_code"],
            },
            headers=headers,
        )
        assert bind_response.status_code == 200
        bind_payload = bind_response.json()
        assert bind_payload["user"]["has_phone"] is True
        assert bind_payload["user"]["user_id"] == guest_payload["user"]["user_id"]

        async def _assert_record_owner():
            async with session_factory() as session:
                record = await session.scalar(
                    select(RecordOrm).where(RecordOrm.id == record_id)
                )
                user = await session.scalar(
                    select(User).where(User.id == bind_payload["user"]["user_id"])
                )
                assert record is not None
                assert user is not None
                assert record.user_id == user.id
                assert user.phone == "13900139000"

        asyncio.run(_assert_record_owner())
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


async def _prepare_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)
