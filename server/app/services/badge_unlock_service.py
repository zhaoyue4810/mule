from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.yaml_loader import yaml_config
from app.models.badge import BadgeDefinition, UserBadge
from app.models.test import Test
from app.models.record import TestRecord


LOCAL_TZ = ZoneInfo("Asia/Shanghai")


@dataclass
class UnlockedBadge:
    badge_key: str
    name: str
    emoji: str
    tier: int = 1


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
        existing_badges_by_id = {item.badge_id: item for item in existing_badges}
        test_count = int(
            await self.db.scalar(
                select(func.count(TestRecord.id)).where(TestRecord.user_id == user_id)
            )
            or 0
        )
        category_rows = (
            await self.db.execute(
                select(Test.category)
                .join(TestRecord, TestRecord.test_id == Test.id)
                .where(TestRecord.user_id == user_id)
                .group_by(Test.category)
            )
        ).all()
        now_local = (unlock_time or datetime.now()).astimezone(LOCAL_TZ)
        merged_metrics = {
            "test_count": test_count,
            "category_count": len(category_rows),
        }
        merged_metrics.update(metrics or {})

        unlocked: list[UnlockedBadge] = []
        for definition in definitions:
            rule_type = str((definition.unlock_rule or {}).get("type") or "").strip().lower()
            if allowed_rule_types is not None and rule_type not in allowed_rule_types:
                continue
            if not self._rule_matched(
                definition.unlock_rule or {},
                merged_metrics,
                now_local,
            ):
                continue
            existing_badge = existing_badges_by_id.get(definition.id)
            if existing_badge is None:
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
                        tier=1,
                    )
                )
                continue

            next_unlock_count = existing_badge.unlock_count + 1
            next_tier = self._resolve_tier(next_unlock_count)
            if next_unlock_count != existing_badge.unlock_count:
                existing_badge.unlock_count = next_unlock_count
            if next_tier > existing_badge.tier:
                existing_badge.tier = next_tier
                unlocked.append(
                    UnlockedBadge(
                        badge_key=definition.badge_key,
                        name=definition.name,
                        emoji=definition.emoji,
                        tier=next_tier,
                    )
                )
        return unlocked

    async def _ensure_default_definitions(self) -> None:
        if not yaml_config._store:
            yaml_config.load_all()

        badges = yaml_config._store.get("badges", {}).get("badges", [])
        existing_definitions = {
            item.badge_key: item
            for item in (
                await self.db.scalars(select(BadgeDefinition))
            )
        }
        for sort_order, item in enumerate(badges, start=1):
            definition = existing_definitions.get(item["code"])
            if definition is None:
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
                continue

            definition.name = item["name"]
            definition.emoji = item.get("emoji", definition.emoji)
            definition.description = item.get("description")
            definition.type = item.get("scope", definition.type)
            definition.unlock_rule = item.get("unlock_rule") or {}
            definition.sort_order = sort_order
            definition.yaml_source = "badges.yaml"
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

        if rule_type == "streak":
            target = int(rule.get("value") or 0)
            return int(metrics.get("daily_streak") or 0) >= target > 0

        if rule_type == "time_range":
            start_hour = int(rule.get("start") or 0)
            end_hour = int(rule.get("end") or 0)
            return self._hour_in_range(now_local.hour, start_hour, end_hour)

        if rule_type == "category_completion":
            target = int(rule.get("value") or 0)
            return int(metrics.get("category_count") or 0) >= target > 0

        if rule_type == "score_threshold":
            target = int(rule.get("value") or 0)
            return float(metrics.get("score_threshold") or 0) >= target > 0

        if rule_type == "speed":
            target = int(rule.get("value") or 0)
            duration = int(metrics.get("duration_seconds") or 0)
            return 0 < duration <= target

        if rule_type == "match_score_above":
            target = int(rule.get("value") or 0)
            return int(metrics.get("match_score") or 0) >= target > 0

        if rule_type == "match_score_exact":
            target = int(rule.get("value") or -1)
            return int(metrics.get("match_score") or -2) == target

        if rule_type == "any_match":
            return int(metrics.get("match_count") or 0) >= 1

        if rule_type == "same_partner_count":
            target = int(rule.get("value") or 0)
            return int(metrics.get("same_partner_count") or 0) >= target > 0

        if rule_type == "complementary_type":
            return bool(metrics.get("complementary_type"))

        if rule_type == "close_dimension":
            return bool(metrics.get("close_dimension"))

        if rule_type == "both_high_score":
            return bool(metrics.get("both_high_score"))

        if rule_type == "first_match":
            return bool(metrics.get("first_match"))

        if rule_type == "invite_count":
            target = int(rule.get("value") or 0)
            return int(metrics.get("invite_count") or 0) >= target > 0

        if rule_type == "average_match_score_above":
            target = int(rule.get("value") or 0)
            return float(metrics.get("average_match_score") or 0) > target > 0

        return False

    @staticmethod
    def _hour_in_range(hour: int, start: int, end: int) -> bool:
        if start == end:
            return True
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end

    @staticmethod
    def _resolve_tier(unlock_count: int) -> int:
        if unlock_count >= 10:
            return 4
        if unlock_count >= 6:
            return 3
        if unlock_count >= 3:
            return 2
        return 1
