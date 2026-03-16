from __future__ import annotations

import random
import string
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import BadgeDefinition, UserBadge
from app.models.match import MatchReport, MatchSession
from app.models.record import TestRecord
from app.models.report import ReportSnapshot
from app.models.test import Test
from app.models.user import User
from app.services.badge_unlock_service import BadgeUnlockService


class MatchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_invite(self, *, user: User, test_code: str) -> dict:
        test = await self._get_match_enabled_test(test_code)
        await self._get_latest_report(user.id, test.id)

        session = MatchSession(
            initiator_id=user.id,
            partner_id=None,
            test_id=test.id,
            status="WAITING",
            invite_code=await self._generate_invite_code(),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return {
            "session_id": session.id,
            "test_code": test.test_code,
            "test_name": test.title,
            "status": session.status,
            "invite_code": session.invite_code,
            "invite_link": self._build_invite_link(session.invite_code),
            "compatibility_score": None,
            "created_at": session.created_at,
            "completed_at": session.completed_at,
            "initiator": self._user_payload(user),
            "share_message": (
                f"我在心测发起了「{test.title}」灵魂匹配，邀请码 {session.invite_code}，"
                "来看看我们的契合度吧。"
            ),
        }

    async def get_invite_detail(self, *, code: str, user: User) -> dict:
        session, test, initiator, partner, report = await self._get_session_bundle_by_code(code)
        requires_test_completion = False
        can_join = False

        if session.partner_id is None and user.id != session.initiator_id:
            can_join = True
            partner_record = await self._find_latest_report_optional(user.id, test.id)
            requires_test_completion = partner_record is None

        return {
            "session_id": session.id,
            "test_code": test.test_code,
            "test_name": test.title,
            "status": session.status,
            "invite_code": session.invite_code,
            "invite_link": self._build_invite_link(session.invite_code),
            "compatibility_score": report.compatibility_score if report else None,
            "created_at": session.created_at,
            "completed_at": session.completed_at,
            "initiator": self._user_payload(initiator),
            "partner": self._user_payload(partner) if partner else None,
            "partner_joined": session.partner_id is not None,
            "requires_test_completion": requires_test_completion,
            "can_join": can_join,
        }

    async def join_invite(self, *, code: str, user: User) -> dict:
        session, test, initiator, _, existing_report = await self._get_session_bundle_by_code(code)
        if session.initiator_id == user.id:
            raise ValueError("You cannot join your own invite")
        if session.partner_id is not None and session.partner_id != user.id:
            raise ValueError("This invite has already been joined")
        if existing_report is not None:
            return {
                "session_id": session.id,
                "status": "COMPLETED",
                "result_ready": True,
                "compatibility_score": existing_report.compatibility_score,
                "unlocked_badges": [],
            }

        initiator_record, initiator_snapshot = await self._get_latest_report(
            initiator.id,
            test.id,
        )
        partner_record, partner_snapshot = await self._get_latest_report(
            user.id,
            test.id,
        )

        match_payload = self._build_match_payload(
            initiator_scores=self._normalize_scores(initiator_snapshot.dimension_scores),
            partner_scores=self._normalize_scores(partner_snapshot.dimension_scores),
        )
        report = MatchReport(
            session_id=session.id,
            initiator_report_id=initiator_record.id,
            partner_report_id=partner_record.id,
            compatibility_score=match_payload["compatibility_score"],
            dimension_comparison={"items": match_payload["dimension_comparison"]},
            analysis=match_payload["analysis"],
        )
        session.partner_id = user.id
        session.status = "COMPLETED"
        session.completed_at = self._as_naive_utc(datetime.now(UTC))
        self.db.add(report)
        await self.db.flush()

        initiator_badges = await self._unlock_duo_badges(
            user_id=initiator.id,
            session=session,
            report=report,
            initiator_scores=match_payload["initiator_scores"],
            partner_scores=match_payload["partner_scores"],
        )
        partner_badges = await self._unlock_duo_badges(
            user_id=user.id,
            session=session,
            report=report,
            initiator_scores=match_payload["partner_scores"],
            partner_scores=match_payload["initiator_scores"],
        )
        await self.db.commit()

        combined_badges = initiator_badges + [
            badge for badge in partner_badges if badge.badge_key not in {item.badge_key for item in initiator_badges}
        ]
        return {
            "session_id": session.id,
            "status": session.status,
            "result_ready": True,
            "compatibility_score": report.compatibility_score,
            "unlocked_badges": [
                {
                    "badge_key": badge.badge_key,
                    "name": badge.name,
                    "emoji": badge.emoji,
                    "unlocked_at": session.completed_at or session.created_at,
                }
                for badge in combined_badges
            ],
        }

    async def get_result(self, *, session_id: int, user: User) -> dict:
        session, test, initiator, partner, report = await self._get_session_bundle_by_id(session_id)
        if user.id not in {session.initiator_id, session.partner_id}:
            raise LookupError(f"Match session not found: {session_id}")
        if partner is None or report is None:
            raise ValueError("Match result is not ready yet")

        comparison_items = list((report.dimension_comparison or {}).get("items") or [])
        unlocked_badges = await self._list_duo_badges(user.id)

        similar_dimensions = [
            item["dim_code"] for item in comparison_items if item["relation"] == "similar"
        ][:3]
        complementary_dimensions = [
            item["dim_code"] for item in comparison_items if item["relation"] == "complementary"
        ][:3]

        return {
            "session_id": session.id,
            "status": session.status,
            "test_code": test.test_code,
            "test_name": test.title,
            "compatibility_score": report.compatibility_score,
            "tier": self._resolve_tier(report.compatibility_score),
            "analysis": report.analysis,
            "created_at": session.created_at,
            "completed_at": session.completed_at,
            "initiator": self._user_payload(initiator),
            "partner": self._user_payload(partner),
            "dimension_comparison": comparison_items,
            "similar_dimensions": similar_dimensions,
            "complementary_dimensions": complementary_dimensions,
            "unlocked_badges": unlocked_badges,
        }

    async def get_history(self, *, user: User) -> dict:
        sessions = list(
            await self.db.scalars(
                select(MatchSession)
                .where(or_(MatchSession.initiator_id == user.id, MatchSession.partner_id == user.id))
                .order_by(MatchSession.created_at.desc(), MatchSession.id.desc())
            )
        )

        items: list[dict] = []
        for session in sessions:
            test = await self.db.scalar(select(Test).where(Test.id == session.test_id))
            report = await self.db.scalar(
                select(MatchReport).where(MatchReport.session_id == session.id)
            )
            partner_id = session.partner_id if session.initiator_id == user.id else session.initiator_id
            partner = (
                await self.db.scalar(select(User).where(User.id == partner_id))
                if partner_id is not None
                else None
            )
            items.append(
                {
                    "session_id": session.id,
                    "test_code": test.test_code if test else "",
                    "test_name": test.title if test else "",
                    "status": session.status,
                    "invite_code": session.invite_code,
                    "invite_link": self._build_invite_link(session.invite_code),
                    "partner": self._user_payload(partner) if partner else None,
                    "compatibility_score": report.compatibility_score if report else None,
                    "tier": self._resolve_tier(report.compatibility_score) if report else None,
                    "created_at": session.created_at,
                    "completed_at": session.completed_at,
                }
            )

        return {
            "items": items,
            "duo_badges": await self._list_duo_badges(user.id),
        }

    async def _unlock_duo_badges(
        self,
        *,
        user_id: int,
        session: MatchSession,
        report: MatchReport,
        initiator_scores: dict[str, float],
        partner_scores: dict[str, float],
    ):
        completed_count = await self._count_completed_matches(user_id)
        same_partner_count = await self._count_same_partner_matches(
            user_id=user_id,
            partner_id=session.partner_id if session.initiator_id == user_id else session.initiator_id,
        )
        invite_partner_count = await self._count_invited_partners(user_id)
        average_match_score = await self._average_match_score(user_id)

        comparison_items = list((report.dimension_comparison or {}).get("items") or [])
        metrics = {
            "match_count": completed_count,
            "match_score": report.compatibility_score,
            "same_partner_count": same_partner_count,
            "first_match": 1 if completed_count == 1 else 0,
            "invite_count": invite_partner_count,
            "average_match_score": average_match_score,
            "close_dimension": 1
            if any(item["difference"] < 5 for item in comparison_items)
            else 0,
            "both_high_score": 1
            if self._average_strength(initiator_scores) >= 85
            and self._average_strength(partner_scores) >= 85
            else 0,
            "complementary_type": 1
            if sum(1 for item in comparison_items if item["difference"] >= 45) >= 2
            else 0,
        }
        return await BadgeUnlockService(self.db).unlock_for_user(
            user_id=user_id,
            metrics=metrics,
            allowed_rule_types={
                "match_score_above",
                "any_match",
                "same_partner_count",
                "complementary_type",
                "close_dimension",
                "both_high_score",
                "first_match",
                "invite_count",
                "average_match_score_above",
                "match_score_exact",
            },
        )

    async def _count_completed_matches(self, user_id: int) -> int:
        sessions = list(
            await self.db.scalars(
                select(MatchSession).where(
                    or_(MatchSession.initiator_id == user_id, MatchSession.partner_id == user_id),
                    MatchSession.status == "COMPLETED",
                )
            )
        )
        return len(sessions)

    async def _count_same_partner_matches(self, *, user_id: int, partner_id: int | None) -> int:
        if partner_id is None:
            return 0
        sessions = list(
            await self.db.scalars(
                select(MatchSession).where(
                    MatchSession.status == "COMPLETED",
                    or_(
                        (MatchSession.initiator_id == user_id) & (MatchSession.partner_id == partner_id),
                        (MatchSession.initiator_id == partner_id) & (MatchSession.partner_id == user_id),
                    ),
                )
            )
        )
        return len(sessions)

    async def _count_invited_partners(self, user_id: int) -> int:
        sessions = list(
            await self.db.scalars(
                select(MatchSession).where(
                    MatchSession.initiator_id == user_id,
                    MatchSession.partner_id.is_not(None),
                    MatchSession.status == "COMPLETED",
                )
            )
        )
        return len({session.partner_id for session in sessions if session.partner_id is not None})

    async def _average_match_score(self, user_id: int) -> float:
        reports: list[int] = []
        sessions = list(
            await self.db.scalars(
                select(MatchSession).where(
                    or_(MatchSession.initiator_id == user_id, MatchSession.partner_id == user_id),
                    MatchSession.status == "COMPLETED",
                )
            )
        )
        for session in sessions:
            report = await self.db.scalar(
                select(MatchReport).where(MatchReport.session_id == session.id)
            )
            if report is not None:
                reports.append(report.compatibility_score)
        if not reports:
            return 0.0
        return sum(reports) / len(reports)

    async def _list_duo_badges(self, user_id: int) -> list[dict]:
        rows = (
            await self.db.execute(
                select(UserBadge, BadgeDefinition)
                .join(BadgeDefinition, BadgeDefinition.id == UserBadge.badge_id)
                .where(UserBadge.user_id == user_id, BadgeDefinition.type == "duo")
                .order_by(UserBadge.created_at.desc(), UserBadge.id.desc())
            )
        ).all()
        return [
            {
                "badge_key": definition.badge_key,
                "name": definition.name,
                "emoji": definition.emoji,
                "unlocked_at": user_badge.created_at,
            }
            for user_badge, definition in rows
        ]

    async def _get_match_enabled_test(self, test_code: str) -> Test:
        test = await self.db.scalar(select(Test).where(Test.test_code == test_code))
        if test is None:
            raise LookupError(f"Match test not found: {test_code}")
        if not test.is_match_enabled:
            raise ValueError(f"Test {test_code} is not available for matching")
        return test

    async def _get_latest_report(self, user_id: int, test_id: int) -> tuple[TestRecord, ReportSnapshot]:
        payload = await self._find_latest_report_optional(user_id, test_id)
        if payload is None:
            raise ValueError("Please finish this test before starting or joining a match")
        return payload

    async def _find_latest_report_optional(
        self,
        user_id: int,
        test_id: int,
    ) -> tuple[TestRecord, ReportSnapshot] | None:
        row = (
            await self.db.execute(
                select(TestRecord, ReportSnapshot)
                .join(ReportSnapshot, ReportSnapshot.record_id == TestRecord.id)
                .where(TestRecord.user_id == user_id, TestRecord.test_id == test_id)
                .order_by(TestRecord.created_at.desc(), TestRecord.id.desc())
            )
        ).first()
        return row if row is not None else None

    async def _get_session_bundle_by_code(
        self,
        code: str,
    ) -> tuple[MatchSession, Test, User, User | None, MatchReport | None]:
        session = await self.db.scalar(
            select(MatchSession).where(MatchSession.invite_code == code.upper())
        )
        if session is None:
            raise LookupError(f"Invite not found: {code}")
        return await self._assemble_session_bundle(session)

    async def _get_session_bundle_by_id(
        self,
        session_id: int,
    ) -> tuple[MatchSession, Test, User, User | None, MatchReport | None]:
        session = await self.db.scalar(
            select(MatchSession).where(MatchSession.id == session_id)
        )
        if session is None:
            raise LookupError(f"Match session not found: {session_id}")
        return await self._assemble_session_bundle(session)

    async def _assemble_session_bundle(
        self,
        session: MatchSession,
    ) -> tuple[MatchSession, Test, User, User | None, MatchReport | None]:
        test = await self.db.scalar(select(Test).where(Test.id == session.test_id))
        initiator = await self.db.scalar(select(User).where(User.id == session.initiator_id))
        partner = (
            await self.db.scalar(select(User).where(User.id == session.partner_id))
            if session.partner_id is not None
            else None
        )
        report = await self.db.scalar(
            select(MatchReport).where(MatchReport.session_id == session.id)
        )
        if test is None or initiator is None:
            raise LookupError("Match session is incomplete")
        return session, test, initiator, partner, report

    async def _generate_invite_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choice(alphabet) for _ in range(6))
            exists = await self.db.scalar(
                select(MatchSession).where(MatchSession.invite_code == code)
            )
            if exists is None:
                return code

    def _normalize_scores(self, raw_scores: dict) -> dict[str, float]:
        normalized: dict[str, float] = {}
        values = [abs(float(value)) for value in (raw_scores or {}).values()]
        max_value = max(values) if values else 1.0
        max_value = max(max_value, 1.0)
        for dim_code, value in (raw_scores or {}).items():
            normalized[str(dim_code)] = round(abs(float(value)) / max_value * 100, 2)
        return normalized

    def _build_match_payload(
        self,
        *,
        initiator_scores: dict[str, float],
        partner_scores: dict[str, float],
    ) -> dict:
        dim_codes = sorted(set(initiator_scores) | set(partner_scores))
        if not dim_codes:
            raise ValueError("Match requires dimension scores from both reports")

        comparison_items: list[dict] = []
        similarity_values: list[float] = []
        complement_values: list[float] = []

        for dim_code in dim_codes:
            initiator_score = float(initiator_scores.get(dim_code, 0.0))
            partner_score = float(partner_scores.get(dim_code, 0.0))
            difference = abs(initiator_score - partner_score)
            similarity = max(0, round(100 - difference))
            complement = max(
                similarity,
                max(0, round(100 - abs((initiator_score + partner_score) - 100))),
            )
            relation = "balanced"
            if difference < 12:
                relation = "similar"
            elif complement >= 80:
                relation = "complementary"

            comparison_items.append(
                {
                    "dim_code": dim_code,
                    "initiator_score": round(initiator_score, 2),
                    "partner_score": round(partner_score, 2),
                    "difference": round(difference, 2),
                    "similarity": similarity,
                    "relation": relation,
                }
            )
            similarity_values.append(similarity)
            complement_values.append(complement)

        similarity_score = sum(similarity_values) / len(similarity_values)
        complement_score = sum(complement_values) / len(complement_values)
        compatibility_score = round(0.6 * similarity_score + 0.4 * complement_score)
        compatibility_score = max(0, min(100, compatibility_score))

        strongest_similarity = [item["dim_code"] for item in comparison_items if item["relation"] == "similar"][:2]
        strongest_complement = [item["dim_code"] for item in comparison_items if item["relation"] == "complementary"][:2]
        analysis = (
            f"你们在 {', '.join(strongest_similarity or [comparison_items[0]['dim_code']])} 上表现出稳定共振，"
            f"在 {', '.join(strongest_complement or [comparison_items[-1]['dim_code']])} 上形成互补拉力。"
            f"整体契合度为 {compatibility_score} 分，属于「{self._resolve_tier(compatibility_score)}」。"
        )

        return {
            "initiator_scores": initiator_scores,
            "partner_scores": partner_scores,
            "dimension_comparison": comparison_items,
            "compatibility_score": compatibility_score,
            "analysis": analysis,
        }

    def _resolve_tier(self, score: int | None) -> str | None:
        if score is None:
            return None
        if score >= 95:
            return "天作之合"
        if score >= 85:
            return "灵魂共振"
        if score >= 75:
            return "默契搭档"
        if score >= 60:
            return "性格各异"
        return "奇妙碰撞"

    def _build_invite_link(self, invite_code: str) -> str:
        return f"/pages/match/invite?code={invite_code}"

    @staticmethod
    def _as_naive_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    def _user_payload(self, user: User | None) -> dict | None:
        if user is None:
            return None
        return {
            "user_id": user.id,
            "nickname": user.nickname,
            "avatar_value": user.avatar_value,
        }

    def _average_strength(self, scores: dict[str, float]) -> float:
        if not scores:
            return 0.0
        return sum(scores.values()) / len(scores)
