from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.app_persona import PersonaCardPayload
from app.services.persona_card_service import PersonaCardService

router = APIRouter(tags=["app-persona"])


@router.get("/profile/persona-card", response_model=PersonaCardPayload)
async def get_persona_card(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PersonaCardPayload:
    return PersonaCardPayload(**(await PersonaCardService(db).get_persona_card(user=user)))
