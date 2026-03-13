from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.admin_content import (
    AdminTestDetail,
    AdminTestSummary,
    AdminTestVersionContent,
    AdminTestVersionContentUpdateRequest,
    AdminTestVersionDetail,
    AdminTestVersionSummary,
    PublishVersionRequest,
)
from app.services.admin_content_service import AdminContentService

router = APIRouter(tags=["admin-content"])


@router.get("/tests", response_model=list[AdminTestSummary])
async def list_tests(db: AsyncSession = Depends(get_db)) -> list[AdminTestSummary]:
    service = AdminContentService(db)
    return [AdminTestSummary(**item) for item in await service.list_tests()]


@router.get("/tests/{test_code}", response_model=AdminTestDetail)
async def get_test_detail(
    test_code: str,
    db: AsyncSession = Depends(get_db),
) -> AdminTestDetail:
    service = AdminContentService(db)
    try:
        detail = await service.get_test_detail(test_code)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminTestDetail(**detail)


@router.get("/tests/{test_code}/versions", response_model=list[AdminTestVersionSummary])
async def list_versions(
    test_code: str,
    db: AsyncSession = Depends(get_db),
) -> list[AdminTestVersionSummary]:
    service = AdminContentService(db)
    versions = await service.list_versions(test_code)
    return [
        AdminTestVersionSummary(
            id=item.id,
            version=item.version,
            status=item.status,
            description=item.description,
            duration_hint=item.duration_hint,
            published_at=item.published_at,
            created_at=item.created_at,
        )
        for item in versions
    ]


@router.get(
    "/tests/{test_code}/versions/{version_id}",
    response_model=AdminTestVersionDetail,
)
async def get_version_detail(
    test_code: str,
    version_id: int,
    db: AsyncSession = Depends(get_db),
) -> AdminTestVersionDetail:
    service = AdminContentService(db)
    try:
        detail = await service.get_version_detail(test_code, version_id=version_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminTestVersionDetail(**detail)


@router.get(
    "/tests/{test_code}/versions/{version_id}/content",
    response_model=AdminTestVersionContent,
)
async def get_version_content(
    test_code: str,
    version_id: int,
    db: AsyncSession = Depends(get_db),
) -> AdminTestVersionContent:
    service = AdminContentService(db)
    try:
        detail = await service.get_version_content(test_code, version_id=version_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AdminTestVersionContent(**detail)


@router.put(
    "/tests/{test_code}/versions/{version_id}/content",
    response_model=AdminTestVersionContent,
)
async def update_version_content(
    test_code: str,
    version_id: int,
    payload: AdminTestVersionContentUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminTestVersionContent:
    service = AdminContentService(db)
    try:
        detail = await service.update_version_content(test_code, version_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AdminTestVersionContent(**detail)


@router.post("/tests/{test_code}/publish", response_model=AdminTestVersionSummary)
async def publish_version(
    test_code: str,
    payload: PublishVersionRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminTestVersionSummary:
    service = AdminContentService(db)
    try:
        version = await service.publish_version(
            test_code,
            version_id=payload.version_id,
            version_number=payload.version,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return AdminTestVersionSummary(
        id=version.id,
        version=version.version,
        status=version.status,
        description=version.description,
        duration_hint=version.duration_hint,
        published_at=version.published_at,
        created_at=version.created_at,
    )
