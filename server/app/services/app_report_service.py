from __future__ import annotations

from math import floor

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AiAnalysis
from app.models.record import TestAnswer, TestRecord
from app.models.report import ReportSnapshot
from app.models.test import Test, TestPersona, TestVersion


class AppReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_report_detail(self, record_id: int) -> dict:
        query = (
            select(ReportSnapshot, TestRecord, Test, TestVersion)
            .join(TestRecord, TestRecord.id == ReportSnapshot.record_id)
            .join(Test, Test.id == TestRecord.test_id)
            .join(TestVersion, TestVersion.id == TestRecord.version_id)
            .where(ReportSnapshot.record_id == record_id)
        )
        row = (await self.db.execute(query)).first()
        if row is None:
            raise LookupError(f"Report not found: {record_id}")

        snapshot, record, test, version = row
        persona = None
        if snapshot.persona_code:
            persona = await self.db.scalar(
                select(TestPersona).where(
                    TestPersona.version_id == version.id,
                    TestPersona.persona_key == snapshot.persona_code,
                )
            )

        answered_count = await self.db.scalar(
            select(func.count(TestAnswer.id)).where(TestAnswer.record_id == record.id)
        )

        dimension_scores = {
            str(key): float(value)
            for key, value in (snapshot.dimension_scores or {}).items()
        }
        sorted_dimensions = sorted(
            dimension_scores.items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        top_dimensions = sorted_dimensions[:3]
        report_json = snapshot.report_json or {}
        persona_keywords = persona.keywords or [] if persona else []
        analysis = await self.db.scalar(
            select(AiAnalysis)
            .where(AiAnalysis.type == "report", AiAnalysis.ref_id == record_id)
            .order_by(AiAnalysis.id.desc())
        )
        radar_dimensions = self._build_radar_dimensions(sorted_dimensions)
        persona_tags = self._build_persona_tags(top_dimensions, persona_keywords)
        soul_weather = self._build_soul_weather(top_dimensions)
        metaphor_cards = self._build_metaphor_cards(
            report_json.get("persona_name"),
            top_dimensions,
        )
        dna_segments = self._build_dna_segments(sorted_dimensions)
        action_guides = self._build_action_guides(sorted_dimensions)
        result_tier = self._build_result_tier(
            snapshot.overall_score,
            answered_count or 0,
        )
        ai_status = self._resolve_ai_status(snapshot.ai_text, analysis.status if analysis else None)
        share_card = self._build_share_card(
            test_name=test.title,
            persona_name=report_json.get("persona_name"),
            result_tier=result_tier,
            top_dimensions=top_dimensions,
            summary=report_json.get("summary", ""),
        )

        return {
            "report_id": snapshot.id,
            "record_id": record.id,
            "test_code": test.test_code,
            "test_name": test.title,
            "version": version.version,
            "total_score": snapshot.overall_score,
            "summary": report_json.get("summary", ""),
            "dimension_scores": dimension_scores,
            "top_dimensions": [
                {"dim_code": dim_code, "score": score}
                for dim_code, score in top_dimensions
            ],
            "radar_dimensions": radar_dimensions,
            "persona_tags": persona_tags,
            "soul_weather": soul_weather,
            "metaphor_cards": metaphor_cards,
            "dna_segments": dna_segments,
            "action_guides": action_guides,
            "result_tier": result_tier,
            "persona": {
                "persona_key": report_json.get("persona_key"),
                "persona_name": report_json.get("persona_name"),
                "description": persona.description if persona else None,
                "keywords": persona_keywords,
            },
            "answered_count": answered_count or 0,
            "duration_seconds": record.duration,
            "ai_status": ai_status,
            "ai_text": snapshot.ai_text or (analysis.content if analysis else None),
            "share_card_url": snapshot.share_card_url,
            "share_card": share_card,
        }

    def _build_radar_dimensions(
        self,
        sorted_dimensions: list[tuple[str, float]],
    ) -> list[dict]:
        if not sorted_dimensions:
            return []

        max_abs_score = max(abs(score) for _, score in sorted_dimensions) or 1.0
        radar_dimensions = []
        for dim_code, score in sorted_dimensions[:5]:
            radar_dimensions.append(
                {
                    "dim_code": dim_code,
                    "label": dim_code.upper(),
                    "score": score,
                    "normalized_score": round(abs(score) / max_abs_score, 4),
                }
            )
        return radar_dimensions

    def _build_persona_tags(
        self,
        top_dimensions: list[tuple[str, float]],
        persona_keywords: list[str],
    ) -> list[dict]:
        tags = [{"label": keyword, "tone": "keyword"} for keyword in persona_keywords[:3]]
        tags.extend(
            {
                "label": f"{dim_code.upper()} 高感知",
                "tone": "dimension",
            }
            for dim_code, _ in top_dimensions[:2]
        )
        return tags[:5]

    def _build_soul_weather(
        self,
        top_dimensions: list[tuple[str, float]],
    ) -> dict:
        if not top_dimensions:
            return {
                "title": "薄雾晴空",
                "mood": "calm",
                "description": "你的结果刚刚开始显影，继续完成更多测试后，灵魂天气会更稳定。",
            }

        dim_code, score = top_dimensions[0]
        if score >= 1.5:
            return {
                "title": "高压晴空",
                "mood": "bright",
                "description": f"{dim_code.upper()} 维度非常突出，你现在更像处在能量清晰、判断果断的状态。",
            }
        if score >= 0:
            return {
                "title": "微光多云",
                "mood": "warm",
                "description": f"{dim_code.upper()} 维度正在主导你的表达方式，整体节奏偏稳定和温和。",
            }
        return {
            "title": "夜航星幕",
            "mood": "deep",
            "description": f"{dim_code.upper()} 维度带着更强的内向沉浸感，说明你近期更偏向向内整理和自我校准。",
        }

    def _build_metaphor_cards(
        self,
        persona_name: str | None,
        top_dimensions: list[tuple[str, float]],
    ) -> list[dict]:
        anchor = top_dimensions[0][0].upper() if top_dimensions else "CORE"
        persona_label = persona_name or "当前画像"
        return [
            {
                "category": "建筑",
                "title": f"{anchor} 灯塔",
                "subtitle": f"{persona_label} 在复杂情境里更容易形成方向感。",
                "emoji": "🏛",
            },
            {
                "category": "动物",
                "title": "夜行灵狐",
                "subtitle": "你擅长在细节变化里捕捉真正重要的信息。",
                "emoji": "🦊",
            },
            {
                "category": "星球",
                "title": "余晖行星",
                "subtitle": "外在节奏温和，但内核一直在持续运转和积累。",
                "emoji": "🪐",
            },
        ]

    def _build_dna_segments(
        self,
        sorted_dimensions: list[tuple[str, float]],
    ) -> list[dict]:
        if not sorted_dimensions:
            return []

        max_abs_score = max(abs(score) for _, score in sorted_dimensions) or 1.0
        return [
            {
                "dim_code": dim_code,
                "label": dim_code.upper(),
                "percentage": min(100, max(8, floor(abs(score) / max_abs_score * 100))),
            }
            for dim_code, score in sorted_dimensions[:5]
        ]

    def _build_action_guides(
        self,
        sorted_dimensions: list[tuple[str, float]],
    ) -> list[dict]:
        if not sorted_dimensions:
            return [
                {
                    "title": "继续采样",
                    "description": "再完成 1 到 2 套不同类别测试，你的报告会更稳定，画像也会更完整。",
                }
            ]

        strongest = sorted_dimensions[0][0].upper()
        weakest = sorted_dimensions[-1][0].upper()
        return [
            {
                "title": f"放大 {strongest} 优势",
                "description": f"把需要 {strongest} 特质的任务放到你状态最好的时段，会更容易做出高质量输出。",
            },
            {
                "title": f"补强 {weakest} 维度",
                "description": f"从低成本的小练习开始，让 {weakest} 维度逐步进入你的日常决策和反馈回路。",
            },
            {
                "title": "观察情境切换",
                "description": "记录你在独处、协作和压力场景里的差异，下一次再看报告时会更容易发现稳定模式。",
            },
        ]

    def _build_result_tier(
        self,
        total_score: int | None,
        answered_count: int,
    ) -> str:
        if not answered_count or total_score is None:
            return "初始显影"

        average_score = total_score / answered_count
        if average_score >= 1.5:
            return "高能定型"
        if average_score >= 0.8:
            return "稳定成像"
        return "渐进解锁"

    def _build_share_card(
        self,
        *,
        test_name: str,
        persona_name: str | None,
        result_tier: str,
        top_dimensions: list[tuple[str, float]],
        summary: str,
    ) -> dict:
        persona_label = persona_name or "你的当前画像"
        primary_dim = top_dimensions[0][0].upper() if top_dimensions else "CORE"
        secondary_dim = top_dimensions[1][0].upper() if len(top_dimensions) > 1 else None
        theme = self._resolve_share_theme(primary_dim)
        highlight_lines = [f"{result_tier} · {persona_label}"]
        highlight_lines.append(f"主导维度：{primary_dim}")
        if secondary_dim:
            highlight_lines.append(f"辅助维度：{secondary_dim}")
        stat_chips = [result_tier, f"主维度 {primary_dim}"]
        if secondary_dim:
            stat_chips.append(f"副维度 {secondary_dim}")

        compact_summary = (summary or "").strip()
        if len(compact_summary) > 46:
            compact_summary = f"{compact_summary[:46]}..."

        share_text = "\n".join(
            [
                f"我刚完成了《{test_name}》",
                f"结果是：{persona_label} · {result_tier}",
                f"主导维度：{primary_dim}",
                compact_summary or "这份报告比我想象中更像现在的自己。",
            ]
        )

        return {
            "theme": theme["theme"],
            "background": theme["background"],
            "title": persona_label,
            "subtitle": f"{test_name} · {result_tier}",
            "accent": primary_dim,
            "badge": theme["badge"],
            "footer": "来自心测 · 今日人格切片",
            "stat_chips": stat_chips,
            "highlight_lines": highlight_lines,
            "share_text": share_text,
        }

    def _resolve_share_theme(self, primary_dim: str) -> dict:
        mapping = {
            "EI": {
                "theme": "dawn",
                "background": "linear-gradient(145deg, #fff0dc, #ffc9a8)",
                "badge": "外放灵感",
            },
            "SN": {
                "theme": "aurora",
                "background": "linear-gradient(145deg, #e9fff2, #b8f0cf)",
                "badge": "感知流动",
            },
            "TF": {
                "theme": "ember",
                "background": "linear-gradient(145deg, #fff1ea, #ffb694)",
                "badge": "判断火花",
            },
            "JP": {
                "theme": "nightfall",
                "background": "linear-gradient(145deg, #edf1ff, #c9d3ff)",
                "badge": "秩序星图",
            },
            "CORE": {
                "theme": "sunset",
                "background": "linear-gradient(145deg, #fff2e7, #ffd9bf)",
                "badge": "当前画像",
            },
        }
        return mapping.get(primary_dim, mapping["CORE"])

    def _resolve_ai_status(self, ai_text: str | None, status: int | None) -> str:
        if ai_text:
            return "COMPLETED"
        if status == 1:
            return "RUNNING"
        if status == 2:
            return "COMPLETED"
        if status == 3:
            return "FAILED"
        return "PENDING"
