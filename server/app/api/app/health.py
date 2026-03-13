from fastapi import APIRouter

from app.core.config import get_settings
from app.core.yaml_loader import yaml_config

router = APIRouter(tags=["system"])


@router.get("/health")
def health_check() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "config": yaml_config.summary(),
    }
