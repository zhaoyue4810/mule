from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.yaml_loader import yaml_config
from app.models.soul import SoulFragmentDefinition, UserSoulFragment


@dataclass
class UnlockedSoulFragment:
    fragment_key: str
    name: str
    emoji: str | None
    category: str
    insight: str | None


class SoulFragmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def unlock_for_user(
        self,
        *,
        user_id: int,
        test_code: str,
    ) -> list[UnlockedSoulFragment]:
        await self._ensure_default_definitions()
        definitions = list(
            await self.db.scalars(
                select(SoulFragmentDefinition).order_by(
                    SoulFragmentDefinition.sort_order.asc(),
                    SoulFragmentDefinition.id.asc(),
                )
            )
        )
        if not definitions:
            return []

        existing_fragment_ids = set(
            await self.db.scalars(
                select(UserSoulFragment.fragment_id).where(
                    UserSoulFragment.user_id == user_id
                )
            )
        )

        unlocked: list[UnlockedSoulFragment] = []
        for definition in definitions:
            if definition.id in existing_fragment_ids:
                continue
            if not self._definition_matched(definition, test_code):
                continue

            self.db.add(
                UserSoulFragment(
                    user_id=user_id,
                    fragment_id=definition.id,
                )
            )
            unlocked.append(
                UnlockedSoulFragment(
                    fragment_key=definition.fragment_key,
                    name=definition.name,
                    emoji=definition.emoji,
                    category=definition.category,
                    insight=definition.insight,
                )
            )

        await self.db.flush()
        return unlocked

    async def list_user_fragments(self, user_id: int) -> list[dict]:
        rows = (
            await self.db.execute(
                select(UserSoulFragment, SoulFragmentDefinition)
                .join(
                    SoulFragmentDefinition,
                    SoulFragmentDefinition.id == UserSoulFragment.fragment_id,
                )
                .where(UserSoulFragment.user_id == user_id)
                .order_by(
                    UserSoulFragment.created_at.desc(),
                    UserSoulFragment.id.desc(),
                )
            )
        ).all()

        return [
            {
                "fragment_key": definition.fragment_key,
                "name": definition.name,
                "emoji": definition.emoji,
                "category": definition.category,
                "insight": definition.insight,
                "unlocked_at": user_fragment.created_at,
            }
            for user_fragment, definition in rows
        ]

    async def build_category_progress(self, user_id: int) -> list[dict]:
        await self._ensure_default_definitions()
        category_specs = self._get_category_specs()
        definitions = list(await self.db.scalars(select(SoulFragmentDefinition)))
        total_by_category: dict[str, int] = {}
        for definition in definitions:
            total_by_category[definition.category] = (
                total_by_category.get(definition.category, 0) + 1
            )

        unlocked_rows = (
            await self.db.execute(
                select(
                    SoulFragmentDefinition.category,
                    func.count(UserSoulFragment.id),
                )
                .join(
                    UserSoulFragment,
                    UserSoulFragment.fragment_id == SoulFragmentDefinition.id,
                )
                .where(UserSoulFragment.user_id == user_id)
                .group_by(SoulFragmentDefinition.category)
            )
        ).all()
        unlocked_by_category = {
            str(category): int(count) for category, count in unlocked_rows
        }

        progress: list[dict] = []
        seen_categories: set[str] = set()
        for item in category_specs:
            category_code = item["code"]
            total_count = int(
                item.get("need") or total_by_category.get(category_code) or 0
            )
            unlocked_count = unlocked_by_category.get(category_code, 0)
            progress.append(
                {
                    "category_code": category_code,
                    "category_name": item["name"],
                    "unlocked_count": unlocked_count,
                    "total_count": total_count,
                    "completed": total_count > 0 and unlocked_count >= total_count,
                }
            )
            seen_categories.add(category_code)

        for category_code, total_count in sorted(total_by_category.items()):
            if category_code in seen_categories:
                continue
            unlocked_count = unlocked_by_category.get(category_code, 0)
            progress.append(
                {
                    "category_code": category_code,
                    "category_name": category_code,
                    "unlocked_count": unlocked_count,
                    "total_count": total_count,
                    "completed": total_count > 0 and unlocked_count >= total_count,
                }
            )
        return progress

    async def _ensure_default_definitions(self) -> None:
        definition_count = int(
            await self.db.scalar(select(func.count(SoulFragmentDefinition.id))) or 0
        )
        if definition_count > 0:
            return

        if not yaml_config._store:
            yaml_config.load_all()

        fragments = yaml_config._store.get("soul_fragments", {}).get("fragments", [])
        for sort_order, item in enumerate(fragments, start=1):
            self.db.add(
                SoulFragmentDefinition(
                    fragment_key=item["code"],
                    name=item["name"],
                    emoji=item.get("emoji"),
                    category=item["category"],
                    required_test_code=item.get("required_test_code"),
                    insight=item.get("insight"),
                    sort_order=sort_order,
                    yaml_source="soul_fragments.yaml",
                )
            )
        await self.db.flush()

    def _definition_matched(
        self,
        definition: SoulFragmentDefinition,
        test_code: str,
    ) -> bool:
        required_test_code = (definition.required_test_code or "").strip().lower()
        if not required_test_code:
            return False
        return required_test_code == test_code.strip().lower()

    def _get_category_specs(self) -> list[dict]:
        if not yaml_config._store:
            yaml_config.load_all()
        return list(yaml_config._store.get("soul_fragments", {}).get("categories", []))
