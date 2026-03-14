from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import TestRecord
from app.models.report import ReportSnapshot
from app.models.test import TestPersona
from app.models.user import User


class PersonaCardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_persona_card(self, *, user: User) -> dict:
        rows = (
            await self.db.execute(
                select(TestRecord, ReportSnapshot)
                .join(ReportSnapshot, ReportSnapshot.record_id == TestRecord.id)
                .where(TestRecord.user_id == user.id)
                .order_by(TestRecord.created_at.desc(), TestRecord.id.desc())
            )
        ).all()
        if not rows:
            return {
                "user_id": user.id,
                "nickname": user.nickname,
                "avatar_value": user.avatar_value,
                "persona_title": "灵魂探索者",
                "soul_signature": "你的画像正在形成，完成更多测试后这里会更清晰。",
                "keywords": ["初始显影"],
                "dimensions": [],
                "weather": self._build_weather(0),
            }

        latest_record, latest_snapshot = rows[0]
        dimension_totals: dict[str, float] = defaultdict(float)
        for _, snapshot in rows:
            for dim_code, score in (snapshot.dimension_scores or {}).items():
                dimension_totals[str(dim_code)] += float(score)
        top_dimensions = sorted(
            dimension_totals.items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        )[:5]
        persona_name = latest_snapshot.report_json.get("persona_name") or "灵魂探索者"
        persona = None
        if latest_snapshot.persona_code:
            persona = await self.db.scalar(
                select(TestPersona).where(
                    TestPersona.version_id == latest_record.version_id,
                    TestPersona.persona_key == latest_snapshot.persona_code,
                )
            )
        keywords = list(persona.keywords or []) if persona and persona.keywords else []
        if not keywords:
            keywords = [f"{dim_code.upper()} 感知" for dim_code, _ in top_dimensions[:3]]
        max_abs = max((abs(score) for _, score in top_dimensions), default=1.0) or 1.0
        normalized_average = (
            sum((abs(score) / max_abs) * 100 for _, score in top_dimensions) / max(1, len(top_dimensions))
        )

        return {
            "user_id": user.id,
            "nickname": user.nickname,
            "avatar_value": user.avatar_value,
            "persona_title": persona_name,
            "soul_signature": (
                persona.soul_signature
                if persona and persona.soul_signature
                else latest_snapshot.report_json.get("summary")
                or "你正在一步步看见自己更稳定的轮廓。"
            ),
            "keywords": keywords[:3],
            "dimensions": [
                {
                    "dim_code": dim_code,
                    "label": dim_code.upper(),
                    "score": round((abs(score) / max_abs) * 100, 2),
                }
                for dim_code, score in top_dimensions
            ],
            "weather": self._build_weather(normalized_average),
        }

    def _build_weather(self, average_score: float) -> dict:
        if average_score >= 85:
            return {"emoji": "☀️", "title": "晴朗", "description": "画像清晰、能量稳定，你对自己的轮廓已经有很强把握。"}
        if average_score >= 75:
            return {"emoji": "⛅", "title": "多云转晴", "description": "大部分特质已经显影，继续采样会更接近稳定的人设名片。"}
        if average_score >= 65:
            return {"emoji": "🌤️", "title": "微风和煦", "description": "你的画像正在逐渐聚焦，既保留流动，也开始形成方向。"}
        return {"emoji": "🌈", "title": "雨后彩虹", "description": "目前还是多彩的探索期，每一次测试都在补上新的线索。"}
