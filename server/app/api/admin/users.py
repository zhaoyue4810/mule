from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.badge import BadgeDefinition, UserBadge
from app.models.match import MatchReport, MatchSession
from app.models.record import TestRecord
from app.models.test import Test
from app.models.user import User
from app.schemas.admin_user import (
    AdminUserBadge,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserMatchRecord,
    AdminUserStatusUpdateRequest,
    AdminUserSummary,
    AdminUserTestRecord,
)

router = APIRouter(tags=["admin-users"])


def _status_to_label(status: int) -> str:
    return "ENABLED" if status == 1 else "DISABLED"


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    keyword: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> AdminUserListResponse:
    filters = []
    if keyword:
        filters.append(User.nickname.ilike(f"%{keyword.strip()}%"))

    total_query = select(func.count(User.id))
    if filters:
        total_query = total_query.where(*filters)
    total = int(await db.scalar(total_query) or 0)

    query = (
        select(User, func.count(TestRecord.id).label("test_count"))
        .outerjoin(TestRecord, TestRecord.user_id == User.id)
        .group_by(User.id)
        .order_by(User.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    if filters:
        query = query.where(*filters)
    rows = await db.execute(query)

    items = [
        AdminUserSummary(
            id=user.id,
            nickname=user.nickname,
            avatar_value=user.avatar_value,
            gender=user.gender,
            created_at=user.created_at,
            test_count=int(test_count or 0),
            status=_status_to_label(user.status),
        )
        for user, test_count in rows.all()
    ]
    return AdminUserListResponse(items=items, total=total, page=page, size=size)


@router.get("/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    test_count = int(
        await db.scalar(select(func.count(TestRecord.id)).where(TestRecord.user_id == user_id))
        or 0
    )

    match_count = int(
        await db.scalar(
            select(func.count(MatchSession.id)).where(
                or_(MatchSession.initiator_id == user_id, MatchSession.partner_id == user_id)
            )
        )
        or 0
    )

    test_record_rows = await db.execute(
        select(
            TestRecord.id,
            Test.title,
            TestRecord.total_score,
            TestRecord.created_at,
        )
        .join(Test, Test.id == TestRecord.test_id)
        .where(TestRecord.user_id == user_id)
        .order_by(TestRecord.created_at.desc())
        .limit(30)
    )
    test_records = [
        AdminUserTestRecord(
            record_id=row.id,
            test_name=row.title,
            total_score=row.total_score,
            completed_at=row.created_at,
        )
        for row in test_record_rows
    ]

    match_rows = await db.execute(
        select(
            MatchSession.id,
            Test.title,
            MatchSession.status,
            MatchReport.compatibility_score,
            MatchSession.created_at,
            MatchSession.completed_at,
        )
        .join(Test, Test.id == MatchSession.test_id)
        .outerjoin(MatchReport, MatchReport.session_id == MatchSession.id)
        .where(or_(MatchSession.initiator_id == user_id, MatchSession.partner_id == user_id))
        .order_by(MatchSession.created_at.desc())
        .limit(30)
    )
    match_records = [
        AdminUserMatchRecord(
            session_id=row.id,
            test_name=row.title,
            status=row.status,
            compatibility_score=row.compatibility_score,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )
        for row in match_rows
    ]

    badge_rows = await db.execute(
        select(
            BadgeDefinition.badge_key,
            BadgeDefinition.name,
            BadgeDefinition.emoji,
            UserBadge.tier,
            UserBadge.unlock_count,
            UserBadge.created_at,
        )
        .join(BadgeDefinition, BadgeDefinition.id == UserBadge.badge_id)
        .where(UserBadge.user_id == user_id)
        .order_by(UserBadge.created_at.desc())
    )
    badges = [
        AdminUserBadge(
            badge_key=row.badge_key,
            name=row.name,
            emoji=row.emoji,
            tier=row.tier,
            unlock_count=row.unlock_count,
            unlocked_at=row.created_at,
        )
        for row in badge_rows
    ]

    return AdminUserDetail(
        id=user.id,
        nickname=user.nickname,
        avatar_value=user.avatar_value,
        gender=user.gender,
        created_at=user.created_at,
        status=_status_to_label(user.status),
        test_count=test_count,
        match_count=match_count,
        badges=badges,
        test_records=test_records,
        match_records=match_records,
    )


@router.put("/{user_id}/status", response_model=AdminUserSummary)
async def update_user_status(
    user_id: int,
    payload: AdminUserStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminUserSummary:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = 1 if payload.status == "ENABLED" else 0
    await db.commit()
    await db.refresh(user)

    test_count = int(
        await db.scalar(select(func.count(TestRecord.id)).where(TestRecord.user_id == user.id))
        or 0
    )
    return AdminUserSummary(
        id=user.id,
        nickname=user.nickname,
        avatar_value=user.avatar_value,
        gender=user.gender,
        created_at=user.created_at,
        test_count=test_count,
        status=_status_to_label(user.status),
    )
