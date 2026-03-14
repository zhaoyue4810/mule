from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.badge import BadgeDefinition
from app.schemas.admin_system import AdminBadgeDefinitionItem

router = APIRouter(tags=["admin-badges"])


@router.get("", response_model=list[AdminBadgeDefinitionItem])
async def list_badges(db: AsyncSession = Depends(get_db)) -> list[AdminBadgeDefinitionItem]:
    rows = await db.scalars(select(BadgeDefinition).order_by(BadgeDefinition.sort_order.asc()))
    return [
        AdminBadgeDefinitionItem(
            badge_key=item.badge_key,
            name=item.name,
            emoji=item.emoji,
            type=item.type,
            unlock_rule=item.unlock_rule,
            yaml_source=item.yaml_source,
        )
        for item in rows
    ]
