from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.yaml_loader import yaml_config


class RuntimeCheckService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def build_readiness_payload(self, db: AsyncSession) -> dict[str, object]:
        config_summary = yaml_config.summary()
        checks: dict[str, object] = {
            "yaml_config": {
                "status": "ok"
                if config_summary.get("interaction_type_count", 0) > 0
                else "error",
                "interaction_type_count": config_summary.get("interaction_type_count", 0),
            },
            "database": {"status": "error"},
            "jwt_secret": {
                "status": (
                    "warning"
                    if self.settings.jwt_secret_key == "change-me"
                    else "ok"
                )
            },
            "wechat_mini_program": {
                "status": "ok"
                if self.settings.wx_appid and self.settings.wx_secret
                else "not_configured"
            },
            "ai_gateway": {
                "dashscope": "configured"
                if self.settings.dashscope_api_key
                else "not_configured",
                "volc": "configured"
                if self.settings.volc_api_key
                else "not_configured",
            },
        }

        try:
            await db.execute(text("SELECT 1"))
            checks["database"] = {"status": "ok"}
        except Exception as exc:
            checks["database"] = {"status": "error", "detail": str(exc)}

        ready = (
            checks["yaml_config"]["status"] == "ok"
            and checks["database"]["status"] == "ok"
        )

        return {
            "status": "ready" if ready else "degraded",
            "service": self.settings.app_name,
            "environment": self.settings.app_env,
            "checks": checks,
        }
