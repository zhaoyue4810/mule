from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.yaml_loader import yaml_config
from app.models.badge import BadgeDefinition, UserBadge
from app.models.record import TestRecord


LOCAL_TZ = ZoneInfo("Asia/Shanghai")


@dataclass
class UnlockedBadge:
    badge_key: str
    name: str
    emoji: str


class BadgeUnlockService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def unlock_for_user(
        self,
        *,
        user_id: int,
        unlock_time: datetime | None = None,
        metrics: dict[str, int] | None = None,
        allowed_rule_types: set[str] | None = None,
    ) -> list[UnlockedBadge]:
        await self._ensure_default_definitions()
        definitions = list(
            await self.db.scalars(
                select(BadgeDefinition).order_by(BadgeDefinition.sort_order.asc())
            )
        )
        if not definitions:
            return []

        existing_badges = list(
            await self.db.scalars(select(UserBadge).where(UserBadge.user_id == user_id))
        )
        existing_badge_ids = {item.badge_id for item in existing_badges}
        test_count = int(
            await self.db.scalar(
                select(func.count(TestRecord.id)).where(TestRecord.user_id == user_id)
            )
            or 0
        )
        now_local = (unlock_time or datetime.now()).astimezone(LOCAL_TZ)
        merged_metrics = {
            "test_count": test_count,
        }
        merged_metrics.update(metrics or {})

        unlocked: list[UnlockedBadge] = []
        for definition in definitions:
            if definition.id in existing_badge_ids:
                continue
            rule_type = str((definition.unlock_rule or {}).get("type") or "").strip().lower()
            if allowed_rule_types is not None and rule_type not in allowed_rule_types:
                continue
            if not self._rule_matched(
                definition.unlock_rule or {},
                merged_metrics,
                now_local,
            ):
                continue
            self.db.add(
                UserBadge(
                    user_id=user_id,
                    badge_id=definition.id,
                    tier=1,
                    unlock_count=1,
                )
            )
            unlocked.append(
                UnlockedBadge(
                    badge_key=definition.badge_key,
                    name=definition.name,
                    emoji=definition.emoji,
                )
            )
        return unlocked

    async def _ensure_default_definitions(self) -> None:
        definition_count = int(
            await self.db.scalar(select(func.count(BadgeDefinition.id))) or 0
        )
        if definition_count > 0:
            return

        if not yaml_config._store:
            yaml_config.load_all()

        badges = yaml_config._store.get("badges", {}).get("badges", [])
        for sort_order, item in enumerate(badges, start=1):
            self.db.add(
                BadgeDefinition(
                    badge_key=item["code"],
                    name=item["name"],
                    emoji=item.get("emoji", "🏅"),
                    description=item.get("description"),
                    type=item.get("scope", "personal"),
                    unlock_rule=item.get("unlock_rule") or {},
                    sort_order=sort_order,
                    yaml_source="badges.yaml",
                )
            )
        await self.db.flush()

    def _rule_matched(
        self,
        rule: dict,
        metrics: dict[str, int],
        now_local: datetime,
    ) -> bool:
        rule_type = str(rule.get("type") or "").strip().lower()
        if not rule_type:
            return False

        if rule_type == "test_count":
            target = int(rule.get("value") or 0)
            return int(metrics.get("test_count") or 0) >= target > 0

        if rule_type == "daily_streak":
            target = int(rule.get("value") or 0)
            return int(metrics.get("daily_streak") or 0) >= target > 0

        if rule_type == "time_range":
            start_hour = int(rule.get("start") or 0)
            end_hour = int(rule.get("end") or 0)
            return self._hour_in_range(now_local.hour, start_hour, end_hour)

        return False

    @staticmethod
    def _hour_in_range(hour: int, start: int, end: int) -> bool:
        if start == end:
            return True
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end
