from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import get_db, get_metadata
from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["config"]["interaction_type_count"] == 15


def test_bootstrap_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/app/bootstrap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["bootstrap_stage"] == "phase_2_content_runtime"
    assert len(payload["interaction_types"]) == 15


def test_readiness_endpoint() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        import asyncio

        async def prepare() -> None:
            async with engine.begin() as conn:
                await conn.run_sync(get_metadata().create_all)

        asyncio.run(prepare())
        client = TestClient(app)

        response = client.get("/health/ready")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["checks"]["database"]["status"] == "ok"
        assert payload["checks"]["yaml_config"]["status"] == "ok"
        assert payload["checks"]["ai_gateway"]["dashscope"] in {"configured", "not_configured"}
        assert payload["checks"]["wechat_mini_program"]["status"] in {"ok", "not_configured"}
    finally:
        app.dependency_overrides.clear()
        import asyncio

        asyncio.run(engine.dispose())


def test_readiness_endpoint_returns_503_when_database_check_fails() -> None:
    class BrokenSession:
        async def execute(self, *_args, **_kwargs):
            raise RuntimeError("database unavailable")

    async def override_get_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)
        response = client.get("/health/ready")

        assert response.status_code == 503
        payload = response.json()
        assert payload["status"] == "degraded"
        assert payload["checks"]["database"]["status"] == "error"
        assert "unavailable" in payload["checks"]["database"]["detail"]
    finally:
        app.dependency_overrides.clear()
