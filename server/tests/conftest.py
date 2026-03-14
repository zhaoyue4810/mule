from __future__ import annotations

import pytest

from app.core.auth import get_admin_user
from app.main import app


@pytest.fixture(autouse=True)
def _override_admin_auth(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("real_admin_auth"):
        yield
        return

    async def _admin() -> dict[str, str]:
        return {"username": "pytest-admin", "role": "admin"}

    app.dependency_overrides[get_admin_user] = _admin
    yield
    app.dependency_overrides.pop(get_admin_user, None)
