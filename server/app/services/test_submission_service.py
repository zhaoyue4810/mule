from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import TestAnswer, TestRecord
from app.models.report import ReportSnapshot
from app.models.test import Option, Question, Test, TestPersona, TestVersion
from app.models.user import User
from app.schemas.app_content import TestSubmitRequest
from app.services.badge_unlock_service import BadgeUnlockService
from app.services.calendar_activity_service import CalendarActivityService
from app.services.score_engine import ScoreEngine
from app.services.soul_fragment_service import SoulFragmentService


class TestSubmissionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def submit(self, test_code: str, payload: TestSubmitRequest) -> dict:
        test, version = await self._get_published_test(test_code)
        user = await self._get_or_create_user(payload)

        questions = list(
            await self.db.scalars(
                select(Question)
                .where(Question.version_id == version.id)
                .order_by(Question.seq.asc(), Question.id.asc())
            )
        )
        self._validate_answer_set(questions, payload.answers)
        question_map = {item.seq: item for item in questions}
        options = list(
            await self.db.scalars(
                select(Option)
                .join(Question, Question.id == Option.question_id)
                .where(Question.version_id == version.id)
                .order_by(Option.seq.asc(), Option.id.asc())
            )
        )
        option_map = {
            (option.question_id, option.option_code or str(option.seq)): option
            for option in options
        }

        selected_answers: list[dict] = []
        dimension_scores: dict[str, float] = {}
        total_score = 0.0

        for item in payload.answers:
            question = question_map.get(item.question_seq)
            if question is None:
                raise ValueError(f"Unknown question seq: {item.question_seq}")

            ScoreEngine.validate_answer_shape(
                question.interaction_type,
                item.option_code,
                item.numeric_value,
                item.ordered_option_codes,
                item.point,
            )

            if item.option_code is not None:
                option_key = item.option_code.strip()
                option = option_map.get((question.id, option_key))
                if option is None:
                    raise ValueError(
                        f"Unknown option for question seq {item.question_seq}: {option_key}"
                    )

                total_score += option.value
                self._apply_option_score(question, option, dimension_scores)
                selected_answers.append(
                    {
                        "question": question,
                        "option": option,
                    }
                )
                continue

            if item.ordered_option_codes is not None:
                ranked_options = self._resolve_ranked_options(
                    question,
                    options=options,
                    ordered_option_codes=item.ordered_option_codes,
                )
                rank_total_score = 0.0
                for index, option in enumerate(ranked_options):
                    normalized_rank = ScoreEngine.normalize_rank_position(
                        index,
                        len(ranked_options),
                    )
                    weighted_value = option.value * normalized_rank
                    rank_total_score += weighted_value
                    self._apply_option_score_with_value(
                        question,
                        option,
                        dimension_scores,
                        weighted_value,
                    )
                total_score += rank_total_score
                selected_answers.append(
                    {
                        "question": question,
                        "ordered_option_codes": item.ordered_option_codes,
                        "ranked_labels": [option.label for option in ranked_options],
                    }
                )
                continue

            if item.point is not None:
                ScoreEngine.validate_point(item.point)
                point_value = self._apply_plot2d_score(
                    question,
                    point=item.point,
                    dimension_scores=dimension_scores,
                )
                total_score += point_value
                selected_answers.append(
                    {
                        "question": question,
                        "point": item.point,
                    }
                )
                continue

            ScoreEngine.validate_numeric_range(
                question.interaction_type,
                item.numeric_value or 0,
                question.config,
            )
            normalized_value = ScoreEngine.normalize_numeric_answer(
                question.interaction_type,
                item.numeric_value or 0,
                question.config,
            )
            total_score += normalized_value
            self._apply_numeric_score(question, normalized_value, dimension_scores)
            selected_answers.append(
                {
                    "question": question,
                    "numeric_value": item.numeric_value,
                    "normalized_value": normalized_value,
                }
            )

        persona = await self._resolve_persona(version.id, dimension_scores)

        record = TestRecord(
            user_id=user.id,
            test_id=test.id,
            version_id=version.id,
            persona_id=persona.id if persona else None,
            scores=dimension_scores,
            total_score=int(total_score),
            duration=payload.duration_seconds,
        )
        self.db.add(record)
        await self.db.flush()

        for item in selected_answers:
            question = item["question"]
            option = item.get("option")
            if option is not None:
                answer_value = {
                    "option_code": option.option_code or str(option.seq),
                    "label": option.label,
                    "value": option.value,
                }
            elif item.get("ordered_option_codes") is not None:
                answer_value = {
                    "ordered_option_codes": item["ordered_option_codes"],
                    "labels": item["ranked_labels"],
                }
            elif item.get("point") is not None:
                answer_value = {
                    "point": item["point"],
                }
            else:
                answer_value = {
                    "numeric_value": item["numeric_value"],
                    "normalized_value": item["normalized_value"],
                }

            self.db.add(
                TestAnswer(
                    record_id=record.id,
                    question_id=question.id,
                    answer_value=answer_value,
                )
            )

        report_summary = self._build_report_summary(test.title, persona, dimension_scores)
        top_dimensions = sorted(
            dimension_scores.items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        )[:3]
        self.db.add(
            ReportSnapshot(
                record_id=record.id,
                dimension_scores=dimension_scores,
                overall_score=int(total_score),
                persona_code=persona.persona_key if persona else None,
                report_json={
                    "test_code": test.test_code,
                    "test_name": test.title,
                    "persona_key": persona.persona_key if persona else None,
                    "persona_name": persona.persona_name if persona else None,
                    "summary": report_summary,
                    "top_dimensions": [
                        {"dim_code": dim_code, "score": score}
                        for dim_code, score in top_dimensions
                    ],
                },
                ai_text=None,
            )
        )

        calendar_service = CalendarActivityService(self.db)
        await calendar_service.record_test_completion(
            user_id=user.id,
            test_record_id=record.id,
        )

        badge_service = BadgeUnlockService(self.db)
        unlocked_badges = await badge_service.unlock_for_user(user_id=user.id)
        soul_fragment_service = SoulFragmentService(self.db)
        unlocked_fragments = await soul_fragment_service.unlock_for_user(
            user_id=user.id,
            test_code=test.test_code,
        )

        await self.db.commit()
        await self.db.refresh(record)

        return {
            "record_id": record.id,
            "user_id": user.id,
            "test_code": test.test_code,
            "version": version.version,
            "total_score": int(total_score),
            "dimension_scores": dimension_scores,
            "persona_key": persona.persona_key if persona else None,
            "persona_name": persona.persona_name if persona else None,
            "report_summary": report_summary,
            "answers": [
                {
                    "question_seq": item["question"].seq,
                    "option_code": (
                        item["option"].option_code or str(item["option"].seq)
                        if item.get("option") is not None
                        else None
                    ),
                    "label": (
                        item["option"].label
                        if item.get("option") is not None
                        else " > ".join(item["ranked_labels"])
                        if item.get("ranked_labels") is not None
                        else f"坐标 ({item['point']['x']:.2f}, {item['point']['y']:.2f})"
                        if item.get("point") is not None
                        else f"数值 {item['numeric_value']}"
                    ),
                }
                for item in selected_answers
            ],
            "unlocked_badges": [
                {
                    "badge_key": item.badge_key,
                    "name": item.name,
                    "emoji": item.emoji,
                }
                for item in unlocked_badges
            ],
            "unlocked_fragments": [
                {
                    "fragment_key": item.fragment_key,
                    "name": item.name,
                    "emoji": item.emoji,
                    "category": item.category,
                    "insight": item.insight,
                }
                for item in unlocked_fragments
            ],
        }

    def _validate_answer_set(
        self,
        questions: list[Question],
        answers,
    ) -> None:
        expected_seqs = {question.seq for question in questions}
        received_seqs = [item.question_seq for item in answers]
        received_seq_set = set(received_seqs)

        if len(received_seqs) != len(received_seq_set):
            raise ValueError("Duplicate answers are not allowed")

        missing_seqs = sorted(expected_seqs - received_seq_set)
        extra_seqs = sorted(received_seq_set - expected_seqs)
        if missing_seqs:
            raise ValueError(f"Missing answers for question seq: {missing_seqs}")
        if extra_seqs:
            raise ValueError(f"Unknown question seq: {extra_seqs}")

    async def _get_published_test(self, test_code: str) -> tuple[Test, TestVersion]:
        query = (
            select(Test, TestVersion)
            .join(TestVersion, TestVersion.test_id == Test.id)
            .where(Test.test_code == test_code, TestVersion.status == "PUBLISHED")
        )
        row = (await self.db.execute(query)).first()
        if row is None:
            raise LookupError(f"Published test not found: {test_code}")
        return row

    async def _get_or_create_user(self, payload: TestSubmitRequest) -> User:
        if payload.user_id is not None:
            user = await self.db.scalar(select(User).where(User.id == payload.user_id))
            if user is None:
                raise LookupError(f"User not found: {payload.user_id}")
            return user

        user = User(
            nickname=payload.nickname or "访客用户",
            avatar_value="🧠",
            onboarding_completed=False,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    @staticmethod
    def _normalize_dimension_code(raw_dim_code: object, *, field_name: str) -> str:
        dim_code = "" if raw_dim_code is None else str(raw_dim_code).strip()
        if not dim_code:
            raise ValueError(f"{field_name} must not be blank")
        return dim_code

    @staticmethod
    def _parse_finite_number(raw_value: object, *, field_name: str) -> float:
        try:
            parsed = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be a finite number") from exc
        ScoreEngine._ensure_finite_number(field_name, parsed)
        return parsed

    def _iter_validated_dim_weights(self, question: Question) -> list[tuple[str, float]]:
        validated: list[tuple[str, float]] = []
        seen_dim_codes: set[str] = set()
        for raw_dim_code, raw_weight in (question.dim_weights or {}).items():
            dim_code = self._normalize_dimension_code(
                raw_dim_code,
                field_name=f"Question seq {question.seq} dim_weights key",
            )
            if dim_code in seen_dim_codes:
                raise ValueError(
                    f"Question seq {question.seq} has duplicate dim_weights key: {dim_code}"
                )
            seen_dim_codes.add(dim_code)
            weight_value = self._parse_finite_number(
                raw_weight,
                field_name=f"Question seq {question.seq} dim_weights[{dim_code}]",
            )
            validated.append((dim_code, weight_value))
        return validated

    def _apply_option_score(
        self,
        question: Question,
        option: Option,
        dimension_scores: dict[str, float],
    ) -> None:
        self._apply_option_score_with_value(
            question,
            option,
            dimension_scores,
            option.value,
        )

    def _apply_option_score_with_value(
        self,
        question: Question,
        option: Option,
        dimension_scores: dict[str, float],
        resolved_value: float,
    ) -> None:
        resolved_value = self._parse_finite_number(
            resolved_value,
            field_name=f"Question seq {question.seq} option score value",
        )
        score_rules = option.score_rules or {}
        if score_rules:
            if not isinstance(score_rules, dict):
                raise ValueError(
                    f"Question seq {question.seq} option {option.option_code or option.seq} "
                    "score_rules must be an object"
                )

            option_key = option.option_code or str(option.seq)
            if "dimension_code" in score_rules or "value" in score_rules:
                dim_code = self._normalize_dimension_code(
                    score_rules.get("dimension_code"),
                    field_name=(
                        f"Question seq {question.seq} option {option_key} "
                        "score_rules.dimension_code"
                    ),
                )
                score_value = self._parse_finite_number(
                    score_rules.get("value", resolved_value),
                    field_name=(
                        f"Question seq {question.seq} option {option_key} "
                        "score_rules.value"
                    ),
                )
                dimension_scores[dim_code] = (
                    dimension_scores.get(dim_code, 0.0) + score_value
                )
                return

        for dim_code, weight_value in self._iter_validated_dim_weights(question):
            dimension_scores[dim_code] = dimension_scores.get(dim_code, 0.0) + (
                resolved_value * weight_value
            )

    def _apply_numeric_score(
        self,
        question: Question,
        normalized_value: float,
        dimension_scores: dict[str, float],
    ) -> None:
        normalized_value = self._parse_finite_number(
            normalized_value,
            field_name=f"Question seq {question.seq} normalized_value",
        )
        validated_dim_weights = self._iter_validated_dim_weights(question)
        if not validated_dim_weights:
            raise ValueError(
                f"Question seq {question.seq} requires non-empty dim_weights"
            )
        for dim_code, weight_value in validated_dim_weights:
            dimension_scores[dim_code] = dimension_scores.get(dim_code, 0.0) + (
                normalized_value * weight_value
            )

    def _resolve_ranked_options(
        self,
        question: Question,
        options: list[Option],
        ordered_option_codes: list[str],
    ) -> list[Option]:
        question_options = [
            option for option in options if option.question_id == question.id
        ]
        option_map = {
            option.option_code or str(option.seq): option for option in question_options
        }
        normalized_codes = [option_code.strip() for option_code in ordered_option_codes]
        if len(normalized_codes) != len(question_options):
            raise ValueError(
                f"Question seq {question.seq} rank answer must include all options"
            )
        if any(not option_code for option_code in normalized_codes):
            raise ValueError(
                f"Question seq {question.seq} rank answer contains blank option code"
            )
        if len(set(normalized_codes)) != len(normalized_codes):
            raise ValueError(f"Question seq {question.seq} rank answer has duplicates")

        ranked_options: list[Option] = []
        for option_code in normalized_codes:
            option = option_map.get(option_code)
            if option is None:
                raise ValueError(
                    f"Unknown rank option for question seq {question.seq}: {option_code}"
                )
            ranked_options.append(option)
        return ranked_options

    def _apply_plot2d_score(
        self,
        question: Question,
        point: dict[str, float],
        dimension_scores: dict[str, float],
    ) -> float:
        validated_dim_weights = self._iter_validated_dim_weights(question)
        if len(validated_dim_weights) < 2:
            raise ValueError(
                f"Question seq {question.seq} plot2d requires at least two dim_weights"
            )
        dims = [item[0] for item in validated_dim_weights]
        dim_weight_map = dict(validated_dim_weights)
        x_value = self._parse_finite_number(
            point["x"],
            field_name=f"Question seq {question.seq} point.x",
        )
        y_value = self._parse_finite_number(
            point["y"],
            field_name=f"Question seq {question.seq} point.y",
        )

        if dims:
            x_dim = dims[0]
            x_weight = dim_weight_map[x_dim]
            dimension_scores[x_dim] = dimension_scores.get(x_dim, 0.0) + (
                x_value * x_weight
            )

        if len(dims) > 1:
            y_dim = dims[1]
            y_weight = dim_weight_map[y_dim]
            dimension_scores[y_dim] = dimension_scores.get(y_dim, 0.0) + (
                y_value * y_weight
            )

        return (x_value + y_value) / 2

    async def _resolve_persona(
        self,
        version_id: int,
        dimension_scores: dict[str, float],
    ) -> TestPersona | None:
        personas = list(
            await self.db.scalars(
                select(TestPersona).where(TestPersona.version_id == version_id)
            )
        )
        if not personas:
            return None

        def persona_score(persona: TestPersona) -> float:
            score = 0.0
            for dim_code, expected in (persona.dim_pattern or {}).items():
                actual = float(dimension_scores.get(dim_code, 0.0))
                if isinstance(expected, (int, float)):
                    score -= abs(actual - float(expected))
                    continue
                if isinstance(expected, str) and len(dim_code) >= 2:
                    positive_key = dim_code[0].upper()
                    negative_key = dim_code[1].upper()
                    actual_side = positive_key if actual >= 0 else negative_key
                    if actual_side == expected.upper():
                        score += 1
                elif str(expected) == str(actual):
                    score += 1
            return score

        return max(personas, key=persona_score)

    def _build_report_summary(
        self,
        test_name: str,
        persona: TestPersona | None,
        dimension_scores: dict[str, float],
    ) -> str:
        lead = (
            f"你完成了《{test_name}》，当前结果偏向 {persona.persona_name}。"
            if persona
            else f"你完成了《{test_name}》，基础结果已经生成。"
        )
        if not dimension_scores:
            return lead
        top_dim = max(dimension_scores.items(), key=lambda item: abs(item[1]))
        return f"{lead} 当前最显著维度是 {top_dim[0]}（{top_dim[1]:.1f}）。"
