from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.import_task import (
    ImportTaskApplyRequest,
    ImportTaskCreateRequest,
    ImportTaskParseRequest,
    ImportTaskResponse,
)
from app.services.import_task_service import ImportTaskService

router = APIRouter(tags=["admin-import"])


@router.get("/tasks", response_model=list[ImportTaskResponse])
async def list_import_tasks(db: AsyncSession = Depends(get_db)) -> list[ImportTaskResponse]:
    service = ImportTaskService(db)
    tasks = await service.list_tasks()
    return [ImportTaskResponse.from_model(task) for task in tasks]


@router.post(
    "/tasks",
    response_model=ImportTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_import_task(
    payload: ImportTaskCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    try:
        task = await service.create_task(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ImportTaskResponse.from_model(task)


@router.get("/tasks/{task_id}", response_model=ImportTaskResponse)
async def get_import_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Import task not found")
    return ImportTaskResponse.from_model(task)


@router.post("/tasks/{task_id}/parse", response_model=ImportTaskResponse)
async def parse_import_task(
    task_id: int,
    payload: ImportTaskParseRequest,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    try:
        task = await service.parse_task(task_id, force=payload.force)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ImportTaskResponse.from_model(task)


@router.post("/tasks/{task_id}/apply", response_model=ImportTaskResponse)
async def apply_import_task(
    task_id: int,
    payload: ImportTaskApplyRequest,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    try:
        task = await service.apply_task(task_id, note=payload.note)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ImportTaskResponse.from_model(task)
