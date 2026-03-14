from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SERVER_DIR
from app.core.database import get_db
from app.models.importing import ImportTask
from app.schemas.import_task import (
    ImportTaskApplyRequest,
    ImportTaskCreateRequest,
    ImportTaskParseRequest,
    ImportTaskPageResponse,
    ImportTaskRejectRequest,
    ImportTaskResponse,
)
from app.services.import_task_service import ImportTaskService

router = APIRouter(tags=["admin-import"])

UPLOAD_DIR = SERVER_DIR / "uploads" / "imports"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _guess_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".docx":
        return "docx"
    if suffix in {".html", ".htm"}:
        return "html"
    raise ValueError("Unsupported file type, only .docx/.html allowed")


@router.post(
    "/upload",
    response_model=ImportTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_import_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    filename = file.filename or "upload.bin"
    try:
        file_type = _guess_file_type(filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    safe_name = f"{uuid4().hex}-{Path(filename).name}"
    target = UPLOAD_DIR / safe_name
    content = await file.read()
    target.write_bytes(content)

    service = ImportTaskService(db)
    task = await service.create_task(
        ImportTaskCreateRequest(file_type=file_type, file_path=str(target), operator_id=0)
    )
    task = await service.parse_task(task.id)
    return ImportTaskResponse.from_model(task)


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
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ImportTaskResponse.from_model(task)


@router.get("/tasks", response_model=ImportTaskPageResponse)
async def list_import_tasks(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ImportTaskPageResponse:
    total = int(await db.scalar(select(func.count(ImportTask.id))) or 0)
    rows = await db.scalars(
        select(ImportTask)
        .order_by(ImportTask.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return ImportTaskPageResponse(
        items=[ImportTaskResponse.from_model(item) for item in rows],
        total=total,
        page=page,
        size=size,
    )


@router.post("/tasks/{task_id}/parse", response_model=ImportTaskResponse)
async def parse_import_task(
    task_id: int,
    payload: ImportTaskParseRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    try:
        task = await service.parse_task(task_id, force=bool(payload and payload.force))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ImportTaskResponse.from_model(task)


@router.post("/tasks/{task_id}/apply", response_model=ImportTaskResponse)
async def apply_import_task(
    task_id: int,
    payload: ImportTaskApplyRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    try:
        task = await service.apply_task(task_id, note=payload.note if payload else None)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ImportTaskResponse.from_model(task)


@router.get("/{task_id}/preview", response_model=ImportTaskResponse)
async def get_import_preview(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    task = await service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Import task not found")
    if not task.preview_json and task.status not in {"FAILED", "REJECTED"}:
        task = await service.parse_task(task_id)
    return ImportTaskResponse.from_model(task)


@router.post("/{task_id}/approve", response_model=ImportTaskResponse)
async def approve_import_task(
    task_id: int,
    payload: ImportTaskApplyRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    try:
        task = await service.apply_task(task_id, note=payload.note if payload else None)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ImportTaskResponse.from_model(task)


@router.post("/{task_id}/reject", response_model=ImportTaskResponse)
async def reject_import_task(
    task_id: int,
    payload: ImportTaskRejectRequest,
    db: AsyncSession = Depends(get_db),
) -> ImportTaskResponse:
    service = ImportTaskService(db)
    try:
        task = await service.reject_task(task_id, reason=payload.reason)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ImportTaskResponse.from_model(task)
