from fastapi import APIRouter

from app.api.app.auth import router as app_auth_router
from app.api.app.ai import router as app_ai_router
from app.api.admin.ai import router as admin_ai_router
from app.api.admin.content import router as admin_content_router
from app.api.admin.importing import router as admin_import_router
from app.api.app.config import router as config_router
from app.api.app.health import router as health_router
from app.api.app.profile import router as app_profile_router
from app.api.app.reports import router as app_reports_router
from app.api.app.tests import router as app_tests_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(app_auth_router, prefix="/api/app")
api_router.include_router(app_ai_router, prefix="/api/app")
api_router.include_router(config_router, prefix="/api/app")
api_router.include_router(app_profile_router, prefix="/api/app")
api_router.include_router(app_reports_router, prefix="/api/app")
api_router.include_router(app_tests_router, prefix="/api/app")
api_router.include_router(admin_ai_router, prefix="/api/admin/ai")
api_router.include_router(admin_import_router, prefix="/api/admin/import")
api_router.include_router(admin_content_router, prefix="/api/admin/content")
