from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.yaml_loader import yaml_config
from app.services.runtime_check_service import RuntimeCheckService

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


@router.get("/health/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    settings = get_settings()
    payload = await RuntimeCheckService(settings).build_readiness_payload(db)
    return JSONResponse(
        status_code=200 if payload["status"] == "ready" else 503,
        content=payload,
    )
