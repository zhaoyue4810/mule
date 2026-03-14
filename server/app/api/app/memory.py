from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.app_memory import MemoryGreetingPayload, MemorySuggestPayload
from app.services.memory_service import MemoryService

router = APIRouter(tags=["app-memory"])


@router.get("/memory/greeting", response_model=MemoryGreetingPayload)
async def get_memory_greeting(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemoryGreetingPayload:
    return MemoryGreetingPayload(**(await MemoryService(db).get_greeting(user=user)))


@router.get("/memory/suggest", response_model=MemorySuggestPayload)
async def get_memory_suggest(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemorySuggestPayload:
    return MemorySuggestPayload(**(await MemoryService(db).get_suggestions(user=user)))
