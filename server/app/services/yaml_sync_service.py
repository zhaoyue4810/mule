from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.database import get_metadata
from app.core.yaml_loader import yaml_config
from app.models.badge import BadgeDefinition
from app.models.calendar import DailySoulQuestion
from app.models.soul import SoulFragmentDefinition
from app.models.test import Dimension, Option, Question, Test, TestPersona, TestVersion


@dataclass
class SyncResult:
    test_code: str
    version_id: int
    created_version: int
    question_count: int
    persona_count: int


@dataclass
class DictionarySyncSummary:
    badge_count: int
    daily_question_count: int
    soul_fragment_count: int


class YamlSyncService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def sync_test(self, test_code: str) -> SyncResult:
        data = yaml_config.get_test(test_code)
        if not data:
            raise ValueError(f"Unknown test_code: {test_code}")

        test = await self._get_or_create_test(data)
        version_number = await self._next_version_number(test.id)
        version = await self._create_version(test.id, version_number, data)

        await self._sync_dimensions(version.id, data.get("dimensions", []))
        await self._sync_questions(version.id, data.get("questions", []))
        await self._sync_personas(version.id, data.get("personas", []))

        await self.db.commit()
        await self.db.refresh(version)

        return SyncResult(
            test_code=test_code,
            version_id=version.id,
            created_version=version.version,
            question_count=len(data.get("questions", [])),
            persona_count=len(data.get("personas", [])),
        )

    async def sync_all_tests(self) -> list[SyncResult]:
        results: list[SyncResult] = []
        for test_code in sorted(yaml_config.get_all_tests()):
            results.append(await self.sync_test(test_code))
        return results

    async def sync_dictionaries(self) -> DictionarySyncSummary:
        badge_count = await self._sync_badges()
        daily_question_count = await self._sync_daily_questions()
        soul_fragment_count = await self._sync_soul_fragments()
        await self.db.commit()
        return DictionarySyncSummary(
            badge_count=badge_count,
            daily_question_count=daily_question_count,
            soul_fragment_count=soul_fragment_count,
        )

    async def _get_or_create_test(self, data: dict) -> Test:
        query = select(Test).where(Test.test_code == data["test_code"])
        test = await self.db.scalar(query)

        if test:
            test.title = data["name"]
            test.category = data["category"]
            test.is_match_enabled = bool(data.get("is_match", False))
            test.yaml_source = data.get("source", "yaml")
            return test

        test = Test(
            test_code=data["test_code"],
            title=data["name"],
            category=data["category"],
            is_match_enabled=bool(data.get("is_match", False)),
            yaml_source=data.get("source", "yaml"),
        )
        self.db.add(test)
        await self.db.flush()
        return test

    async def _next_version_number(self, test_id: int) -> int:
        query = select(func.max(TestVersion.version)).where(TestVersion.test_id == test_id)
        current = await self.db.scalar(query)
        return (current or 0) + 1

    async def _create_version(
        self, test_id: int, version_number: int, data: dict
    ) -> TestVersion:
        version = TestVersion(
            test_id=test_id,
            version=version_number,
            status="DRAFT",
            description=data.get("description"),
            duration_hint=f'{data.get("duration_minutes", "")}分钟'
            if data.get("duration_minutes")
            else None,
        )
        self.db.add(version)
        await self.db.flush()
        return version

    async def _sync_dimensions(
        self, version_id: int, dimensions: Iterable[dict]
    ) -> None:
        for index, item in enumerate(dimensions, start=1):
            self.db.add(
                Dimension(
                    version_id=version_id,
                    dim_code=item["code"],
                    dim_name=item["name"],
                    sort_order=index,
                )
            )
        await self.db.flush()

    async def _sync_questions(self, version_id: int, questions: Iterable[dict]) -> None:
        for question_data in questions:
            question = Question(
                version_id=version_id,
                question_code=question_data.get("code"),
                seq=question_data["seq"],
                question_text=question_data["title"],
                interaction_type=question_data["interaction_type"],
                emoji=question_data.get("emoji"),
                config=self._build_question_config(question_data),
                dim_weights=question_data.get("dimension_weights", {}),
            )
            self.db.add(question)
            await self.db.flush()

            for index, option_data in enumerate(question_data.get("options", []), start=1):
                score_rules = None
                dimension_code = option_data.get("dimension_code")
                if dimension_code:
                    score_rules = {
                        "dimension_code": dimension_code,
                        "value": option_data.get("value", 0),
                    }

                self.db.add(
                    Option(
                        question_id=question.id,
                        option_code=option_data.get("code"),
                        seq=index,
                        label=option_data["text"],
                        emoji=option_data.get("emoji"),
                        value=float(option_data.get("value", 0)),
                        score_rules=score_rules,
                        ext_config=None,
                    )
                )

        await self.db.flush()

    async def _sync_personas(self, version_id: int, personas: Iterable[dict]) -> None:
        for item in personas:
            self.db.add(
                TestPersona(
                    version_id=version_id,
                    persona_key=item["code"],
                    persona_name=item["name"],
                    dim_pattern=item["dim_pattern"],
                )
            )
        await self.db.flush()

    def _build_question_config(self, question_data: dict) -> dict | None:
        config: dict[str, object] = {}
        for key in ("scene", "tip", "labels", "words", "axisX", "axisY"):
            if key in question_data:
                config[key] = question_data[key]
        return config or None

    async def _sync_badges(self) -> int:
        badges = yaml_config._store.get("badges", {}).get("badges", [])
        for sort_order, item in enumerate(badges, start=1):
            query = select(BadgeDefinition).where(BadgeDefinition.badge_key == item["code"])
            badge = await self.db.scalar(query)
            if badge is None:
                badge = BadgeDefinition(
                    badge_key=item["code"],
                    name=item["name"],
                    emoji=item.get("emoji", "🏅"),
                    description=item.get("description"),
                    type=item.get("scope", "personal"),
                    unlock_rule=item["unlock_rule"],
                    sort_order=sort_order,
                    yaml_source="badges.yaml",
                )
                self.db.add(badge)
            else:
                badge.name = item["name"]
                badge.emoji = item.get("emoji", badge.emoji)
                badge.type = item.get("scope", badge.type)
                badge.unlock_rule = item["unlock_rule"]
                badge.sort_order = sort_order
        await self.db.flush()
        return len(badges)

    async def _sync_daily_questions(self) -> int:
        questions = yaml_config._store.get("daily_questions", {}).get("questions", [])
        for sort_order, item in enumerate(questions, start=1):
            query = select(DailySoulQuestion).where(
                DailySoulQuestion.question_text == item["text"]
            )
            question = await self.db.scalar(query)
            insights = item.get("insights") or {
                str(index): option for index, option in enumerate(item["options"])
            }
            if question is None:
                question = DailySoulQuestion(
                    question_text=item["text"],
                    options=item["options"],
                    insights=insights,
                    sort_order=sort_order,
                    yaml_source="daily_questions.yaml",
                )
                self.db.add(question)
            else:
                question.options = item["options"]
                question.insights = insights
                question.sort_order = sort_order
        await self.db.flush()
        return len(questions)

    async def _sync_soul_fragments(self) -> int:
        fragments = yaml_config._store.get("soul_fragments", {}).get("fragments", [])
        for sort_order, item in enumerate(fragments, start=1):
            query = select(SoulFragmentDefinition).where(
                SoulFragmentDefinition.fragment_key == item["code"]
            )
            fragment = await self.db.scalar(query)
            if fragment is None:
                fragment = SoulFragmentDefinition(
                    fragment_key=item["code"],
                    name=item["name"],
                    emoji=item.get("emoji"),
                    category=item["category"],
                    required_test_code=item.get("required_test_code"),
                    insight=item.get("insight"),
                    sort_order=sort_order,
                    yaml_source="soul_fragments.yaml",
                )
                self.db.add(fragment)
            else:
                fragment.name = item["name"]
                fragment.emoji = item.get("emoji")
                fragment.category = item["category"]
                fragment.required_test_code = item.get("required_test_code")
                fragment.insight = item.get("insight")
                fragment.sort_order = sort_order
        await self.db.flush()
        return len(fragments)


async def sync_all(database_url: str | None = None) -> list[SyncResult]:
    settings = get_settings()
    db_url = database_url or settings.database_url
    engine = create_async_engine(db_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    yaml_config.load_all()

    async with engine.begin() as conn:
        await conn.run_sync(get_metadata().create_all)

    async with session_factory() as session:
        service = YamlSyncService(session)
        await service.sync_dictionaries()
        results = await service.sync_all_tests()

    await engine.dispose()
    return results


def main() -> None:
    results = asyncio.run(sync_all())
    for item in results:
        print(
            f"[OK] synced {item.test_code} -> version {item.created_version} "
            f"(questions={item.question_count}, personas={item.persona_count})"
        )


if __name__ == "__main__":
    main()
