from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_db, get_metadata
from app.main import app
from app.models.test import (
    Dimension,
    Option,
    Question,
    Test as MatchCaseOrm,
    TestVersion as MatchVersionCaseOrm,
)


async def _prepare_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)


async def _create_match_test(session_factory) -> None:
    async with session_factory() as session:
        test = MatchCaseOrm(
            test_code="duo_case",
            title="双人默契测试",
            category="relationship",
            is_match_enabled=True,
            participant_count=20,
            sort_order=1,
        )
        session.add(test)
        await session.flush()

        version = MatchVersionCaseOrm(
            test_id=test.id,
            version=1,
            status="PUBLISHED",
            description="匹配功能测试",
            duration_hint="3分钟",
            cover_gradient="sunset",
            report_template_code="duo_case_v1",
        )
        session.add(version)
        await session.flush()

        session.add_all(
            [
                Dimension(version_id=version.id, dim_code="heart", dim_name="心动", max_score=100, sort_order=1),
                Dimension(version_id=version.id, dim_code="trust", dim_name="信任", max_score=100, sort_order=2),
            ]
        )
        await session.flush()

        question = Question(
            version_id=version.id,
            question_code="q1",
            seq=1,
            question_text="你最期待怎样的关系互动？",
            interaction_type="bubble",
            dim_weights={"heart": 1},
        )
        session.add(question)
        await session.flush()

        session.add_all(
            [
                Option(
                    question_id=question.id,
                    option_code="a",
                    seq=1,
                    label="稳定陪伴",
                    value=1.0,
                    score_rules={"dimension_code": "heart", "value": 1},
                ),
                Option(
                    question_id=question.id,
                    option_code="b",
                    seq=2,
                    label="热烈冒险",
                    value=0.2,
                    score_rules={"dimension_code": "trust", "value": 0.2},
                ),
            ]
        )
        await session.commit()


def test_match_flow_creates_result_and_history() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        asyncio.run(_prepare_db(engine))
        asyncio.run(_create_match_test(session_factory))
        client = TestClient(app)

        initiator_auth = client.post("/api/app/auth/guest", json={"nickname": "发起人"})
        partner_auth = client.post("/api/app/auth/guest", json={"nickname": "加入人"})
        initiator_headers = {"Authorization": f"Bearer {initiator_auth.json()['access_token']}"}
        partner_headers = {"Authorization": f"Bearer {partner_auth.json()['access_token']}"}

        for headers in (initiator_headers, partner_headers):
            submit_response = client.post(
                "/api/app/tests/duo_case/submit",
                json={
                    "duration_seconds": 12,
                    "answers": [{"question_seq": 1, "option_code": "a"}],
                },
                headers=headers,
            )
            assert submit_response.status_code == 200

        create_response = client.post(
            "/api/app/match/create",
            json={"test_code": "duo_case"},
            headers=initiator_headers,
        )
        assert create_response.status_code == 200
        create_payload = create_response.json()
        assert create_payload["invite_code"]

        invite_response = client.get(
            f"/api/app/match/invite/{create_payload['invite_code']}",
            headers=partner_headers,
        )
        assert invite_response.status_code == 200
        assert invite_response.json()["can_join"] is True

        join_response = client.post(
            f"/api/app/match/join/{create_payload['invite_code']}",
            headers=partner_headers,
        )
        assert join_response.status_code == 200
        join_payload = join_response.json()
        assert join_payload["result_ready"] is True
        assert join_payload["compatibility_score"] >= 95

        result_response = client.get(
            f"/api/app/match/result/{create_payload['session_id']}",
            headers=initiator_headers,
        )
        assert result_response.status_code == 200
        result_payload = result_response.json()
        assert result_payload["tier"] == "天作之合"
        assert result_payload["initiator"]["nickname"] == "发起人"
        assert result_payload["partner"]["nickname"] == "加入人"
        assert result_payload["dimension_comparison"][0]["dim_code"] == "heart"

        history_response = client.get("/api/app/match/history", headers=initiator_headers)
        assert history_response.status_code == 200
        history_payload = history_response.json()
        assert len(history_payload["items"]) == 1
        badge_keys = {item["badge_key"] for item in history_payload["duo_badges"]}
        assert "perfect_match" in badge_keys
        assert "soul_resonance" in badge_keys
        assert "first_encounter" in badge_keys
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())


def test_match_badges_include_repeat_partner_and_average_score() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        asyncio.run(_prepare_db(engine))
        asyncio.run(_create_match_test(session_factory))
        client = TestClient(app)

        initiator_auth = client.post("/api/app/auth/guest", json={"nickname": "Alice"})
        partner_auth = client.post("/api/app/auth/guest", json={"nickname": "Bob"})
        initiator_headers = {"Authorization": f"Bearer {initiator_auth.json()['access_token']}"}
        partner_headers = {"Authorization": f"Bearer {partner_auth.json()['access_token']}"}

        for headers in (initiator_headers, partner_headers):
            submit_response = client.post(
                "/api/app/tests/duo_case/submit",
                json={
                    "duration_seconds": 8,
                    "answers": [{"question_seq": 1, "option_code": "a"}],
                },
                headers=headers,
            )
            assert submit_response.status_code == 200

        for _ in range(3):
            create_response = client.post(
                "/api/app/match/create",
                json={"test_code": "duo_case"},
                headers=initiator_headers,
            )
            invite_code = create_response.json()["invite_code"]
            join_response = client.post(
                f"/api/app/match/join/{invite_code}",
                headers=partner_headers,
            )
            assert join_response.status_code == 200

        history_response = client.get("/api/app/match/history", headers=initiator_headers)
        assert history_response.status_code == 200
        badge_keys = {item["badge_key"] for item in history_response.json()["duo_badges"]}
        assert "rainbow_bridge" in badge_keys
        assert "soulmate_average" in badge_keys
    finally:
        app.dependency_overrides.clear()
        asyncio.run(engine.dispose())
