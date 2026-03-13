from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test import Dimension, Option, Question, Test, TestPersona, TestVersion
from app.schemas.admin_content import AdminTestVersionContentUpdateRequest


class AdminContentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_tests(self) -> list[dict]:
        query = (
            select(
                Test.test_code,
                Test.title,
                Test.category,
                Test.is_match_enabled,
                func.count(TestVersion.id).label("version_count"),
            )
            .join(TestVersion, TestVersion.test_id == Test.id, isouter=True)
            .group_by(Test.id)
            .order_by(Test.test_code)
        )
        rows = (await self.db.execute(query)).all()
        return [
            {
                "test_code": row.test_code,
                "title": row.title,
                "category": row.category,
                "is_match_enabled": row.is_match_enabled,
                "version_count": row.version_count,
            }
            for row in rows
        ]

    async def list_versions(self, test_code: str) -> list[TestVersion]:
        query = (
            select(TestVersion)
            .join(Test, Test.id == TestVersion.test_id)
            .where(Test.test_code == test_code)
            .order_by(TestVersion.version.desc())
        )
        return list(await self.db.scalars(query))

    async def get_test_detail(self, test_code: str) -> dict:
        test = await self.db.scalar(select(Test).where(Test.test_code == test_code))
        if test is None:
            raise LookupError(f"Test not found: {test_code}")

        published = await self.db.scalar(
            select(TestVersion)
            .where(TestVersion.test_id == test.id, TestVersion.status == "PUBLISHED")
            .order_by(TestVersion.version.desc())
        )
        return {
            "test_code": test.test_code,
            "title": test.title,
            "category": test.category,
            "is_match_enabled": test.is_match_enabled,
            "participant_count": test.participant_count,
            "sort_order": test.sort_order,
            "yaml_source": test.yaml_source,
            "published_version_id": published.id if published else None,
            "published_version": published.version if published else None,
        }

    async def get_version_detail(
        self,
        test_code: str,
        *,
        version_id: int | None = None,
        version_number: int | None = None,
    ) -> dict:
        test = await self.db.scalar(select(Test).where(Test.test_code == test_code))
        if test is None:
            raise LookupError(f"Test not found: {test_code}")

        query = select(TestVersion).where(TestVersion.test_id == test.id)
        if version_id is not None:
            query = query.where(TestVersion.id == version_id)
        elif version_number is not None:
            query = query.where(TestVersion.version == version_number)
        else:
            query = query.order_by(TestVersion.version.desc())

        version = await self.db.scalar(query)
        if version is None:
            raise LookupError(f"Version not found for test: {test_code}")

        question_count = await self.db.scalar(
            select(func.count(Question.id)).where(Question.version_id == version.id)
        )
        dimension_count = await self.db.scalar(
            select(func.count(Dimension.id)).where(Dimension.version_id == version.id)
        )
        persona_count = await self.db.scalar(
            select(func.count(TestPersona.id)).where(TestPersona.version_id == version.id)
        )

        return {
            "id": version.id,
            "test_code": test.test_code,
            "title": test.title,
            "category": test.category,
            "version": version.version,
            "status": version.status,
            "description": version.description,
            "duration_hint": version.duration_hint,
            "cover_gradient": version.cover_gradient,
            "report_template_code": version.report_template_code,
            "published_at": version.published_at,
            "created_at": version.created_at,
            "question_count": question_count or 0,
            "dimension_count": dimension_count or 0,
            "persona_count": persona_count or 0,
            "is_published": version.status == "PUBLISHED",
        }

    async def get_version_content(
        self,
        test_code: str,
        *,
        version_id: int | None = None,
        version_number: int | None = None,
    ) -> dict:
        test, version = await self._get_test_and_version(
            test_code,
            version_id=version_id,
            version_number=version_number,
        )

        dimensions = list(
            await self.db.scalars(
                select(Dimension)
                .where(Dimension.version_id == version.id)
                .order_by(Dimension.sort_order.asc(), Dimension.id.asc())
            )
        )
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

        personas = list(
            await self.db.scalars(
                select(TestPersona)
                .where(TestPersona.version_id == version.id)
                .order_by(TestPersona.id.asc())
            )
        )

        return {
            "id": version.id,
            "test_code": test.test_code,
            "title": test.title,
            "category": test.category,
            "is_match_enabled": test.is_match_enabled,
            "participant_count": test.participant_count,
            "sort_order": test.sort_order,
            "version": version.version,
            "status": version.status,
            "description": version.description,
            "duration_hint": version.duration_hint,
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
            "questions": [
                {
                    "question_code": item.question_code,
                    "seq": item.seq,
                    "question_text": item.question_text,
                    "interaction_type": item.interaction_type,
                    "emoji": item.emoji,
                    "config": item.config,
                    "dim_weights": item.dim_weights,
                    "options": [
                        {
                            "option_code": option.option_code,
                            "seq": option.seq,
                            "label": option.label,
                            "emoji": option.emoji,
                            "value": option.value,
                            "score_rules": option.score_rules,
                            "ext_config": option.ext_config,
                        }
                        for option in options_by_question.get(item.id, [])
                    ],
                }
                for item in questions
            ],
            "personas": [
                {
                    "persona_key": item.persona_key,
                    "persona_name": item.persona_name,
                    "emoji": item.emoji,
                    "rarity_percent": item.rarity_percent,
                    "description": item.description,
                    "soul_signature": item.soul_signature,
                    "keywords": item.keywords or [],
                    "dim_pattern": item.dim_pattern,
                    "capsule_prompt": item.capsule_prompt,
                }
                for item in personas
            ],
        }

    async def update_version_content(
        self,
        test_code: str,
        version_id: int,
        payload: AdminTestVersionContentUpdateRequest,
    ) -> dict:
        test, version = await self._get_test_and_version(test_code, version_id=version_id)
        if version.status not in {"DRAFT", "IMPORTED_DRAFT"}:
            raise ValueError(f"Version status {version.status!r} cannot be edited")

        test.title = payload.title
        test.category = payload.category
        test.is_match_enabled = payload.is_match_enabled
        test.participant_count = payload.participant_count
        test.sort_order = payload.sort_order

        version.description = payload.description
        version.duration_hint = payload.duration_hint
        version.cover_gradient = payload.cover_gradient
        version.report_template_code = payload.report_template_code

        question_ids = list(
            await self.db.scalars(
                select(Question.id).where(Question.version_id == version.id)
            )
        )
        if question_ids:
            await self.db.execute(delete(Option).where(Option.question_id.in_(question_ids)))
        await self.db.execute(delete(Question).where(Question.version_id == version.id))
        await self.db.execute(delete(Dimension).where(Dimension.version_id == version.id))
        await self.db.execute(
            delete(TestPersona).where(TestPersona.version_id == version.id)
        )

        for item in payload.dimensions:
            self.db.add(
                Dimension(
                    version_id=version.id,
                    dim_code=item.dim_code,
                    dim_name=item.dim_name,
                    max_score=item.max_score,
                    sort_order=item.sort_order,
                )
            )

        await self.db.flush()

        for item in payload.questions:
            question = Question(
                version_id=version.id,
                question_code=item.question_code,
                seq=item.seq,
                question_text=item.question_text,
                interaction_type=item.interaction_type,
                emoji=item.emoji,
                config=item.config,
                dim_weights=item.dim_weights,
            )
            self.db.add(question)
            await self.db.flush()

            for option in item.options:
                self.db.add(
                    Option(
                        question_id=question.id,
                        option_code=option.option_code,
                        seq=option.seq,
                        label=option.label,
                        emoji=option.emoji,
                        value=option.value,
                        score_rules=option.score_rules,
                        ext_config=option.ext_config,
                    )
                )

        for item in payload.personas:
            self.db.add(
                TestPersona(
                    version_id=version.id,
                    persona_key=item.persona_key,
                    persona_name=item.persona_name,
                    emoji=item.emoji,
                    rarity_percent=item.rarity_percent,
                    description=item.description,
                    soul_signature=item.soul_signature,
                    keywords=item.keywords,
                    dim_pattern=item.dim_pattern,
                    capsule_prompt=item.capsule_prompt,
                )
            )

        await self.db.commit()
        return await self.get_version_content(test_code, version_id=version.id)

    async def publish_version(
        self,
        test_code: str,
        *,
        version_id: int | None = None,
        version_number: int | None = None,
    ) -> TestVersion:
        test = await self.db.scalar(select(Test).where(Test.test_code == test_code))
        if test is None:
            raise LookupError(f"Test not found: {test_code}")

        query = select(TestVersion).where(TestVersion.test_id == test.id)
        if version_id is not None:
            query = query.where(TestVersion.id == version_id)
        elif version_number is not None:
            query = query.where(TestVersion.version == version_number)
        else:
            query = query.order_by(TestVersion.version.desc())

        target = await self.db.scalar(query)
        if target is None:
            raise LookupError(f"Version not found for test: {test_code}")

        if target.status not in {"DRAFT", "IMPORTED_DRAFT", "PUBLISHED"}:
            raise ValueError(f"Version status {target.status!r} cannot be published")

        all_versions = await self.db.scalars(
            select(TestVersion).where(TestVersion.test_id == test.id)
        )
        published_at = datetime.now(timezone.utc)

        for item in all_versions:
            if item.id == target.id:
                item.status = "PUBLISHED"
                item.published_at = published_at
            elif item.status == "PUBLISHED":
                item.status = "ARCHIVED"

        await self.db.commit()
        await self.db.refresh(target)
        return target

    async def _get_test_and_version(
        self,
        test_code: str,
        *,
        version_id: int | None = None,
        version_number: int | None = None,
    ) -> tuple[Test, TestVersion]:
        test = await self.db.scalar(select(Test).where(Test.test_code == test_code))
        if test is None:
            raise LookupError(f"Test not found: {test_code}")

        query = select(TestVersion).where(TestVersion.test_id == test.id)
        if version_id is not None:
            query = query.where(TestVersion.id == version_id)
        elif version_number is not None:
            query = query.where(TestVersion.version == version_number)
        else:
            query = query.order_by(TestVersion.version.desc())

        version = await self.db.scalar(query)
        if version is None:
            raise LookupError(f"Version not found for test: {test_code}")

        return test, version
