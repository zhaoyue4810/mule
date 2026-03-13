from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.ai import AiAnalysis
from app.models.ai import AiPromptTemplate
from app.models.record import TestAnswer
from app.models.report import ReportSnapshot
from app.models.record import TestRecord
from app.models.test import Test, TestPersona, TestVersion
from app.services.ai_gateway import AiGateway
from app.services.prompt_template_service import PromptTemplateService


AI_STATUS_PENDING = 0
AI_STATUS_RUNNING = 1
AI_STATUS_COMPLETED = 2
AI_STATUS_FAILED = 3


class ReportAiService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.prompt_template_service = PromptTemplateService(db)
        self.ai_gateway = AiGateway()

    async def enqueue_report_analysis(self, record_id: int) -> int:
        snapshot = await self.db.scalar(
            select(ReportSnapshot).where(ReportSnapshot.record_id == record_id)
        )
        if snapshot is None:
            raise LookupError(f"Report not found: {record_id}")

        analysis = await self.db.scalar(
            select(AiAnalysis)
            .where(AiAnalysis.type == "report", AiAnalysis.ref_id == record_id)
            .order_by(AiAnalysis.id.desc())
        )
        if analysis is None:
            analysis = AiAnalysis(
                type="report",
                ref_id=record_id,
                provider="fallback",
                model_used="local-template-v1",
                prompt_version="report-fallback-v1",
                provider_errors=[],
                error_message=None,
                started_at=None,
                completed_at=None,
                content="",
                status=AI_STATUS_PENDING,
            )
            self.db.add(analysis)
        else:
            analysis.provider = "fallback"
            analysis.model_used = "local-template-v1"
            analysis.prompt_version = "report-fallback-v1"
            analysis.provider_errors = []
            analysis.error_message = None
            analysis.started_at = None
            analysis.completed_at = None
            analysis.content = ""
            analysis.status = AI_STATUS_PENDING
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis.id

    async def get_report_ai_status(self, record_id: int) -> dict:
        snapshot = await self.db.scalar(
            select(ReportSnapshot).where(ReportSnapshot.record_id == record_id)
        )
        if snapshot is None:
            raise LookupError(f"Report not found: {record_id}")

        analysis = await self.db.scalar(
            select(AiAnalysis)
            .where(AiAnalysis.type == "report", AiAnalysis.ref_id == record_id)
            .order_by(AiAnalysis.id.desc())
        )
        if analysis is None:
            return {
                "record_id": record_id,
                "status": "PENDING",
                "provider": None,
                "model_used": None,
                "content": snapshot.ai_text,
                "updated": False,
            }

        return {
            "record_id": record_id,
            "status": self._status_label(analysis.status),
            "provider": analysis.provider,
            "model_used": analysis.model_used,
            "content": snapshot.ai_text or analysis.content or None,
            "updated": bool(snapshot.ai_text),
        }

    @classmethod
    async def run_report_analysis_job(
        cls,
        session_factory: async_sessionmaker[AsyncSession],
        record_id: int,
    ) -> None:
        async with session_factory() as db:
            service = cls(db)
            analysis = await db.scalar(
                select(AiAnalysis)
                .where(AiAnalysis.type == "report", AiAnalysis.ref_id == record_id)
                .order_by(AiAnalysis.id.desc())
            )
            snapshot = await db.scalar(
                select(ReportSnapshot).where(ReportSnapshot.record_id == record_id)
            )
            if analysis is None or snapshot is None:
                return

            analysis.status = AI_STATUS_RUNNING
            analysis.error_message = None
            analysis.started_at = datetime.now(timezone.utc)
            analysis.completed_at = None
            await db.commit()

            try:
                result = await service._generate_ai_analysis(record_id, snapshot)
                analysis.provider = result["provider"]
                analysis.model_used = result["model_used"]
                analysis.prompt_version = result["prompt_version"]
                analysis.prompt_tokens = result.get("prompt_tokens")
                analysis.output_tokens = result.get("output_tokens")
                analysis.provider_errors = result.get("provider_errors") or []
                analysis.error_message = None
                analysis.content = result["content"]
                analysis.status = AI_STATUS_COMPLETED
                analysis.completed_at = datetime.now(timezone.utc)
                snapshot.ai_text = result["content"]
                await db.commit()
            except Exception as exc:
                analysis.status = AI_STATUS_FAILED
                analysis.error_message = str(exc)
                analysis.provider_errors = [str(exc)]
                analysis.content = f"AI fallback failed: {exc}"
                analysis.completed_at = datetime.now(timezone.utc)
                await db.commit()

    async def _generate_ai_analysis(
        self,
        record_id: int,
        snapshot: ReportSnapshot,
    ) -> dict:
        row = (
            await self.db.execute(
                select(TestRecord, Test, TestVersion)
                .join(Test, Test.id == TestRecord.test_id)
                .join(TestVersion, TestVersion.id == TestRecord.version_id)
                .where(TestRecord.id == record_id)
            )
        ).first()
        if row is None:
            raise LookupError(f"Record not found: {record_id}")

        record, test, version = row
        report_json = snapshot.report_json or {}
        persona_name = report_json.get("persona_name") or "当前画像"
        summary = report_json.get("summary") or "你的结果已经显影。"
        top_dimensions = report_json.get("top_dimensions") or []
        first_dimension = top_dimensions[0]["dim_code"].upper() if top_dimensions else "CORE"
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

        keywords = " / ".join((persona.keywords or [])[:3]) if persona else "独特 / 细腻 / 稳定"
        duration_text = f"{record.duration} 秒" if record.duration else "一次专注完成"
        fallback_text = (
            f"在《{test.title}》里，你当前最接近「{persona_name}」。"
            f"{summary}"
            f"这次结果里最鲜明的线索来自 {first_dimension} 维度，说明你最近在判断、表达和能量分配上，"
            f"都更容易围绕这个核心特征展开。"
            f"如果把这份结果翻译成行动建议，可以先继续放大自己已经稳定显现的优势，再在低分维度上做小步练习。"
            f"你的关键词是：{keywords}。"
            f"这份分析基于你本次 {duration_text} 的作答数据生成，后续完成更多测试后，整体画像会更完整。"
        )
        template = await self._resolve_report_template(version.report_template_code)
        context = {
            "test_name": test.title,
            "persona_name": persona_name,
            "summary": summary,
            "top_dimension": first_dimension,
            "keywords": keywords,
            "total_score": snapshot.overall_score or record.total_score or 0,
            "answered_count": answered_count or 0,
            "duration_seconds": record.duration or "",
        }
        return await self.ai_gateway.generate_from_template(
            template=template,
            context=context,
            fallback_text=fallback_text,
        )

    async def _resolve_report_template(
        self,
        report_template_code: str | None,
    ) -> AiPromptTemplate:
        if report_template_code:
            try:
                return await self.prompt_template_service.get_active_template(
                    report_template_code
                )
            except LookupError:
                pass
        return await self.prompt_template_service.get_active_template("report_analysis_v1")

    def _status_label(self, status: int) -> str:
        if status == AI_STATUS_RUNNING:
            return "RUNNING"
        if status == AI_STATUS_COMPLETED:
            return "COMPLETED"
        if status == AI_STATUS_FAILED:
            return "FAILED"
        return "PENDING"
