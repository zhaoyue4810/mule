from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
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
        assert auth_payload["user"]["onboarding_completed"] is False

        headers = {"Authorization": f"Bearer {auth_payload['access_token']}"}

        me_response = client.get("/api/app/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_payload = me_response.json()
        assert me_payload["user_id"] == auth_payload["user"]["user_id"]
        assert me_payload["nickname"] == "H5 访客"
        assert me_payload["onboarding_completed"] is False

        onboarding_response = client.get(
            "/api/app/profile/me/onboarding",
            headers=headers,
        )
        assert onboarding_response.status_code == 200
        onboarding_payload = onboarding_response.json()
        assert onboarding_payload["nickname"] == "H5 访客"
        assert onboarding_payload["onboarding_completed"] is False

        update_onboarding_response = client.put(
            "/api/app/profile/me/onboarding",
            headers=headers,
            json={
                "nickname": "正式昵称",
                "avatar_value": "🌟",
                "bio": "喜欢观察自己和别人。",
                "gender": 1,
                "birth_year": 1996,
                "birth_month": 5,
            },
        )
        assert update_onboarding_response.status_code == 200
        updated_onboarding = update_onboarding_response.json()
        assert updated_onboarding["nickname"] == "正式昵称"
        assert updated_onboarding["avatar_value"] == "🌟"
        assert updated_onboarding["onboarding_completed"] is True

        refreshed_me_response = client.get("/api/app/auth/me", headers=headers)
        assert refreshed_me_response.status_code == 200
        refreshed_me_payload = refreshed_me_response.json()
        assert refreshed_me_payload["nickname"] == "正式昵称"
        assert refreshed_me_payload["onboarding_completed"] is True

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

        daily_question_response = client.get(
            "/api/app/profile/me/daily-question",
            headers=headers,
        )
        assert daily_question_response.status_code == 200
        daily_question_payload = daily_question_response.json()
        assert daily_question_payload["question_id"] >= 1
        assert daily_question_payload["answered"] is False

        answer_response = client.post(
            "/api/app/profile/me/daily-question",
            json={
                "question_id": daily_question_payload["question_id"],
                "answer_index": 1,
            },
            headers=headers,
        )
        assert answer_response.status_code == 200
        answered_payload = answer_response.json()
        assert answered_payload["answered"] is True
        assert answered_payload["selected_index"] == 1
        assert answered_payload["insight"]
        assert answered_payload["current_streak"] == 1
        assert answered_payload["best_streak"] == 1
        assert answered_payload["unlocked_badges"] == []
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


def test_wechat_mini_program_login_merges_guest_assets_into_wechat_user() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    settings = get_settings()
    original_appid = settings.wx_appid
    original_secret = settings.wx_secret
    settings.wx_appid = "wx-test-appid"
    settings.wx_secret = "wx-test-secret"

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
                "description": "微信归并测试版本",
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
                "personas": [],
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

        with patch(
            "app.services.auth_service.AuthService._exchange_wechat_code",
            new=AsyncMock(return_value={"openid": "openid-a", "unionid": "unionid-a"}),
        ):
            login_response = client.post(
                "/api/app/auth/wechat/mini-program",
                json={
                    "code": "mock-code",
                    "nickname": "微信昵称",
                    "avatar_value": "🌈",
                },
                headers=headers,
            )

        assert login_response.status_code == 200
        login_payload = login_response.json()
        assert login_payload["user"]["user_id"] == guest_payload["user"]["user_id"]
        assert login_payload["user"]["has_openid"] is True
        assert login_payload["user"]["is_guest"] is False

        async def _assert_record_owner():
            async with session_factory() as session:
                record = await session.scalar(
                    select(RecordOrm).where(RecordOrm.id == record_id)
                )
                user = await session.scalar(
                    select(User).where(User.id == login_payload["user"]["user_id"])
                )
                assert record is not None
                assert user is not None
                assert record.user_id == user.id
                assert user.openid == "openid-a"
                assert user.unionid == "unionid-a"
                assert user.nickname == "微信昵称"

        asyncio.run(_assert_record_owner())
    finally:
        settings.wx_appid = original_appid
        settings.wx_secret = original_secret
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_wechat_mini_program_login_reuses_existing_unionid_user() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    settings = get_settings()
    original_appid = settings.wx_appid
    original_secret = settings.wx_secret
    settings.wx_appid = "wx-test-appid"
    settings.wx_secret = "wx-test-secret"

    try:
        import asyncio

        asyncio.run(_prepare_db(engine))

        async def _prepare_existing_user():
            async with session_factory() as session:
                user = User(
                    unionid="shared-unionid",
                    nickname="已有微信用户",
                    avatar_value="🧠",
                    onboarding_completed=True,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user.id

        existing_user_id = asyncio.run(_prepare_existing_user())
        client = TestClient(app)

        with patch(
            "app.services.auth_service.AuthService._exchange_wechat_code",
            new=AsyncMock(
                return_value={
                    "openid": "new-openid",
                    "unionid": "shared-unionid",
                }
            ),
        ):
            login_response = client.post(
                "/api/app/auth/wechat/mini-program",
                json={
                    "code": "mock-code",
                    "nickname": "刷新后的昵称",
                    "avatar_value": "🌙",
                },
            )

        assert login_response.status_code == 200
        login_payload = login_response.json()
        assert login_payload["user"]["user_id"] == existing_user_id
        assert login_payload["user"]["has_openid"] is True

        async def _assert_user_reused():
            async with session_factory() as session:
                user = await session.scalar(select(User).where(User.id == existing_user_id))
                assert user is not None
                assert user.openid == "new-openid"
                assert user.unionid == "shared-unionid"
                assert user.nickname == "刷新后的昵称"
                assert user.avatar_value == "🌙"

        asyncio.run(_assert_user_reused())
    finally:
        settings.wx_appid = original_appid
        settings.wx_secret = original_secret
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
