from __future__ import annotations

import asyncio
import json
import sys

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.yaml_loader import yaml_config
from app.services.runtime_check_service import RuntimeCheckService


async def main() -> int:
    settings = get_settings()
    yaml_config.load_all()
    session_factory = get_session_factory()

    async with session_factory() as session:
        payload = await RuntimeCheckService(settings).build_readiness_payload(session)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
