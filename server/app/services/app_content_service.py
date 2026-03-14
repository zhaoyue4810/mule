from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.yaml_loader import yaml_config
from app.models.test import Dimension, Option, Question, Test, TestPersona, TestVersion


class AppContentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_published_tests(self) -> list[dict]:
        question_count_subquery = (
            select(func.count(Question.id))
            .where(Question.version_id == TestVersion.id)
            .scalar_subquery()
        )
        query = (
            select(
                Test.test_code,
                Test.title,
                Test.category,
                Test.is_match_enabled,
                Test.participant_count,
                TestVersion.version,
                TestVersion.duration_hint,
                TestVersion.cover_gradient,
                question_count_subquery.label("question_count"),
            )
            .join(TestVersion, TestVersion.test_id == Test.id)
            .where(TestVersion.status == "PUBLISHED")
            .order_by(Test.sort_order.asc(), Test.id.asc())
        )
        rows = (await self.db.execute(query)).all()
        return [
            {
                "test_code": row.test_code,
                "name": row.title,
                "category": row.category,
                "is_match_enabled": row.is_match_enabled,
                "participant_count": row.participant_count,
                "version": row.version,
                "question_count": row.question_count,
                "duration_hint": row.duration_hint,
                "cover_gradient": row.cover_gradient,
            }
            for row in rows
        ]

    async def get_published_test_detail(self, test_code: str) -> dict:
        query = (
            select(Test, TestVersion)
            .join(TestVersion, TestVersion.test_id == Test.id)
            .where(Test.test_code == test_code, TestVersion.status == "PUBLISHED")
        )
        row = (await self.db.execute(query)).first()
        if row is None:
            raise LookupError(f"Published test not found: {test_code}")

        test, version = row
        dimensions = list(
            await self.db.scalars(
                select(Dimension)
                .where(Dimension.version_id == version.id)
                .order_by(Dimension.sort_order.asc(), Dimension.id.asc())
            )
        )
        personas = list(
            await self.db.scalars(
                select(TestPersona)
                .where(TestPersona.version_id == version.id)
                .order_by(TestPersona.id.asc())
            )
        )
        question_count = await self.db.scalar(
            select(func.count(Question.id)).where(Question.version_id == version.id)
        )

        return {
            "test_code": test.test_code,
            "name": test.title,
            "category": test.category,
            "is_match_enabled": test.is_match_enabled,
            "participant_count": test.participant_count,
            "sort_order": test.sort_order,
            "version": version.version,
            "question_count": question_count or 0,
            "dimension_count": len(dimensions),
            "persona_count": len(personas),
            "duration_hint": version.duration_hint,
            "description": version.description,
            "cover_gradient": version.cover_gradient,
            "report_template_code": version.report_template_code,
            "dimensions": [
                {
                    "dim_code": item.dim_code,
                    "dim_name": item.dim_name,
                    "max_score": item.max_score,
                    "sort_order": item.sort_order,
                }
                for item in dimensions
            ],
            "personas": [
                {
                    "persona_key": item.persona_key,
                    "persona_name": item.persona_name,
                    "emoji": item.emoji,
                    "rarity_percent": item.rarity_percent,
                    "description": item.description,
                    "keywords": item.keywords or [],
                }
                for item in personas
            ],
        }

    async def get_published_test_questionnaire(self, test_code: str) -> dict:
        query = (
            select(Test, TestVersion)
            .join(TestVersion, TestVersion.test_id == Test.id)
            .where(Test.test_code == test_code, TestVersion.status == "PUBLISHED")
        )
        row = (await self.db.execute(query)).first()
        if row is None:
            raise LookupError(f"Published test not found: {test_code}")

        test, version = row
        questions = list(
            await self.db.scalars(
                select(Question)
                .where(Question.version_id == version.id)
                .order_by(Question.seq.asc(), Question.id.asc())
            )
        )
        question_ids = [item.id for item in questions]
        options_by_question: dict[int, list[Option]] = {}
        if question_ids:
            options = list(
                await self.db.scalars(
                    select(Option)
                    .where(Option.question_id.in_(question_ids))
                    .order_by(Option.seq.asc(), Option.id.asc())
                )
            )
            for option in options:
                options_by_question.setdefault(option.question_id, []).append(option)

        return {
            "test_code": test.test_code,
            "name": test.title,
            "category": test.category,
            "version": version.version,
            "duration_hint": version.duration_hint,
            "question_count": len(questions),
            "questions": [
                {
                    "question_code": item.question_code,
                    "seq": item.seq,
                    "question_text": item.question_text,
                    "interaction_type": item.interaction_type,
                    "emoji": item.emoji,
                    "config": self._build_runtime_question_config(
                        item.interaction_type,
                        item.config,
                    ),
                    "dim_weights": item.dim_weights,
                    "options": [
                        {
                            "option_code": option.option_code,
                            "seq": option.seq,
                            "label": option.label,
                            "emoji": option.emoji,
                            "value": option.value,
                        }
                        for option in options_by_question.get(item.id, [])
                    ],
                }
                for item in questions
            ],
        }

    @staticmethod
    def _build_runtime_question_config(
        interaction_type: str,
        question_config: dict | None,
    ) -> dict | None:
        interaction_types = yaml_config.get_interaction_types()
        type_meta = interaction_types.get(interaction_type, {})
        default_config = type_meta.get("default_config")

        merged: dict = {}
        if isinstance(default_config, dict):
            merged.update(default_config)
        if isinstance(question_config, dict):
            merged.update(question_config)

        return merged or None
