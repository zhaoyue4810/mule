from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_db, get_metadata
from app.main import app


def test_calendar_month_year_stats_and_mood_api() -> None:
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

        auth_response = client.post(
            "/api/app/auth/guest",
            json={"nickname": "日历访客"},
        )
        assert auth_response.status_code == 200
        access_token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        today = datetime.now()
        record_date = today.date().isoformat()

        mood_response = client.post(
            "/api/app/calendar/mood",
            headers=headers,
            json={
                "mood_level": 4,
                "record_date": record_date,
            },
        )
        assert mood_response.status_code == 200
        mood_payload = mood_response.json()
        assert mood_payload["active_days"] == 1
        assert mood_payload["current_streak"] >= 1
        assert mood_payload["best_streak"] >= 1

        month_response = client.get(
            f"/api/app/calendar/month?year={today.year}&month={today.month}",
            headers=headers,
        )
        assert month_response.status_code == 200
        month_payload = month_response.json()
        assert month_payload["year"] == today.year
        assert month_payload["month"] == today.month
        assert any(item["date"] == record_date for item in month_payload["items"])
        day_item = next(item for item in month_payload["items"] if item["date"] == record_date)
        assert day_item["mood_level"] == 4
        assert day_item["events"][0]["source"] == "mood"

        year_response = client.get(
            f"/api/app/calendar/year?year={today.year}",
            headers=headers,
        )
        assert year_response.status_code == 200
        year_payload = year_response.json()
        assert year_payload["year"] == today.year
        assert any(item["date"] == record_date for item in year_payload["items"])

        stats_response = client.get(
            f"/api/app/calendar/stats?year={today.year}",
            headers=headers,
        )
        assert stats_response.status_code == 200
        stats_payload = stats_response.json()
        assert stats_payload["active_days"] == 1
        assert stats_payload["average_mood"] == 4.0
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


async def _prepare_db(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)
