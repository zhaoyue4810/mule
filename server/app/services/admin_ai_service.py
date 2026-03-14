from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AiAnalysis, AiPromptTemplate, AiPromptTemplateHistory
from app.services.report_ai_service import ReportAiService
from app.services.prompt_template_service import PromptTemplateService


class AdminAiService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.prompt_template_service = PromptTemplateService(db)

    async def list_tasks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        task_type: str | None = None,
        status: str | None = None,
        provider: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict:
        page = max(page, 1)
        page_size = max(1, min(page_size, 100))

        query = select(AiAnalysis)
        count_query = select(func.count(AiAnalysis.id))

        if task_type:
            query = query.where(AiAnalysis.type == task_type)
            count_query = count_query.where(AiAnalysis.type == task_type)

        if status:
            mapped_status = self._status_value(status)
            query = query.where(AiAnalysis.status == mapped_status)
            count_query = count_query.where(AiAnalysis.status == mapped_status)

        if provider:
            query = query.where(AiAnalysis.provider == provider)
            count_query = count_query.where(AiAnalysis.provider == provider)
        if date_from:
            query = query.where(AiAnalysis.created_at >= date_from)
            count_query = count_query.where(AiAnalysis.created_at >= date_from)
        if date_to:
            query = query.where(AiAnalysis.created_at <= date_to)
            count_query = count_query.where(AiAnalysis.created_at <= date_to)

        query = query.order_by(AiAnalysis.id.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(await self.db.scalars(query))
        total = int(await self.db.scalar(count_query) or 0)

        return {
            "items": [
                self._serialize_task_summary(item)
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_task_detail(self, task_id: int) -> dict:
        item = await self.db.scalar(select(AiAnalysis).where(AiAnalysis.id == task_id))
        if item is None:
            raise LookupError(f"AI task not found: {task_id}")

        payload = self._serialize_task_summary(item)
        payload["provider_errors"] = list(item.provider_errors or [])
        payload["content"] = item.content
        return payload

    async def get_task_overview(self) -> dict:
        items = list(await self.db.scalars(select(AiAnalysis)))
        status_counter = Counter(self._status_label(item.status) for item in items)
        provider_counter = Counter(item.provider or "unknown" for item in items)
        fallback_runs = sum(1 for item in items if (item.provider or "").lower() == "fallback")
        failed_runs = status_counter.get("FAILED", 0)
        return {
            "total": len(items),
            "pending": status_counter.get("PENDING", 0),
            "running": status_counter.get("RUNNING", 0),
            "completed": status_counter.get("COMPLETED", 0),
            "failed": failed_runs,
            "fallback_runs": fallback_runs,
            "failed_runs": failed_runs,
            "providers": dict(provider_counter),
        }

    async def get_task_metrics(self) -> dict:
        return await self.get_task_metrics_by_bucket(bucket="day")

    async def get_task_metrics_by_bucket(self, *, bucket: str = "day") -> dict:
        items = list(await self.db.scalars(select(AiAnalysis)))
        status_counter = Counter(self._status_label(item.status) for item in items)
        total = len(items)
        completed = status_counter.get("COMPLETED", 0)
        failed = status_counter.get("FAILED", 0)
        running = status_counter.get("RUNNING", 0)
        pending = status_counter.get("PENDING", 0)
        fallback_runs = sum(1 for item in items if (item.provider or "").lower() == "fallback")

        durations = sorted(
            int(max(0.0, (item.completed_at - item.started_at).total_seconds() * 1000))
            for item in items
            if item.started_at and item.completed_at
        )
        avg_duration_ms = int(sum(durations) / len(durations)) if durations else 0
        p95_duration_ms = 0
        if durations:
            percentile_index = min(len(durations) - 1, max(0, int(len(durations) * 0.95) - 1))
            p95_duration_ms = durations[percentile_index]

        cutoff = datetime.now(UTC) - timedelta(hours=24)
        tasks_last_24h = sum(
            1
            for item in items
            if item.created_at and self._as_utc(item.created_at) >= cutoff
        )
        failures_last_24h = sum(
            1
            for item in items
            if item.created_at
            and self._as_utc(item.created_at) >= cutoff
            and self._status_label(item.status) == "FAILED"
        )

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "success_rate": round(completed / total, 4) if total else 0.0,
            "failure_rate": round(failed / total, 4) if total else 0.0,
            "fallback_rate": round(fallback_runs / total, 4) if total else 0.0,
            "avg_duration_ms": avg_duration_ms,
            "p95_duration_ms": p95_duration_ms,
            "tasks_last_24h": tasks_last_24h,
            "failures_last_24h": failures_last_24h,
            "series": self._build_metric_series(items, bucket=bucket),
        }

    async def list_prompt_templates(self) -> list[dict]:
        await self.prompt_template_service.ensure_defaults()
        items = list(
            await self.db.scalars(
                select(AiPromptTemplate).order_by(
                    AiPromptTemplate.scene.asc(),
                    AiPromptTemplate.template_code.asc(),
                )
            )
        )
        return [
            {
                "id": item.id,
                "template_code": item.template_code,
                "scene": item.scene,
                "system_prompt": item.system_prompt,
                "user_prompt_tpl": item.user_prompt_tpl,
                "model_tier": item.model_tier,
                "temperature": float(item.temperature),
                "max_tokens": item.max_tokens,
                "version": item.version,
                "is_active": item.is_active,
                "created_at": item.created_at,
            }
            for item in items
        ]

    async def update_prompt_template(self, template_id: int, payload) -> dict:
        template = await self.db.scalar(
            select(AiPromptTemplate).where(AiPromptTemplate.id == template_id)
        )
        if template is None:
            raise LookupError(f"Prompt template not found: {template_id}")

        await self.prompt_template_service.snapshot_template(template)

        template.system_prompt = payload.system_prompt
        template.user_prompt_tpl = payload.user_prompt_tpl
        template.model_tier = payload.model_tier
        template.temperature = payload.temperature
        template.max_tokens = payload.max_tokens
        template.is_active = payload.is_active
        if payload.bump_version:
            template.version += 1

        await self.db.commit()
        await self.db.refresh(template)
        return {
            "id": template.id,
            "template_code": template.template_code,
            "scene": template.scene,
            "system_prompt": template.system_prompt,
            "user_prompt_tpl": template.user_prompt_tpl,
            "model_tier": template.model_tier,
            "temperature": float(template.temperature),
            "max_tokens": template.max_tokens,
            "version": template.version,
            "is_active": template.is_active,
            "created_at": template.created_at,
        }

    async def list_prompt_template_history(self, template_id: int) -> list[dict]:
        template = await self.db.scalar(
            select(AiPromptTemplate).where(AiPromptTemplate.id == template_id)
        )
        if template is None:
            raise LookupError(f"Prompt template not found: {template_id}")
        items = list(
            await self.db.scalars(
                select(AiPromptTemplateHistory)
                .where(AiPromptTemplateHistory.template_id == template_id)
                .order_by(AiPromptTemplateHistory.version.desc(), AiPromptTemplateHistory.id.desc())
            )
        )
        current = AiPromptTemplateHistory(
            template_id=template.id,
            template_code=template.template_code,
            scene=template.scene,
            system_prompt=template.system_prompt,
            user_prompt_tpl=template.user_prompt_tpl,
            model_tier=template.model_tier,
            temperature=float(template.temperature),
            max_tokens=template.max_tokens,
            version=template.version,
            is_active=template.is_active,
        )
        items = [current, *items]
        return [
            {
                "id": item.id or 0,
                "template_id": item.template_id,
                "template_code": item.template_code,
                "scene": item.scene,
                "system_prompt": item.system_prompt,
                "user_prompt_tpl": item.user_prompt_tpl,
                "model_tier": item.model_tier,
                "temperature": float(item.temperature),
                "max_tokens": item.max_tokens,
                "version": item.version,
                "is_active": item.is_active,
                "created_at": item.created_at or template.created_at,
            }
            for item in items
        ]

    async def compare_prompt_template_versions(
        self,
        template_id: int,
        *,
        from_version: int | None = None,
        to_version: int | None = None,
    ) -> dict:
        history = await self.list_prompt_template_history(template_id)
        ordered = sorted(history, key=lambda item: item["version"])
        if not ordered:
            raise LookupError(f"Prompt template not found: {template_id}")
        target_after = next(
            (item for item in ordered if item["version"] == (to_version or ordered[-1]["version"])),
            ordered[-1],
        )
        target_before_version = from_version if from_version is not None else max(
            ordered[0]["version"], target_after["version"] - 1
        )
        target_before = next(
            (item for item in ordered if item["version"] == target_before_version),
            ordered[0],
        )
        return {
            "template_id": template_id,
            "from_version": target_before["version"],
            "to_version": target_after["version"],
            "system_prompt_before": target_before["system_prompt"],
            "system_prompt_after": target_after["system_prompt"],
            "user_prompt_before": target_before["user_prompt_tpl"],
            "user_prompt_after": target_after["user_prompt_tpl"],
        }

    async def retry_task(self, task_id: int) -> dict:
        item = await self.db.scalar(select(AiAnalysis).where(AiAnalysis.id == task_id))
        if item is None:
            raise LookupError(f"AI task not found: {task_id}")
        if item.type != "report":
            raise ValueError("Only report tasks can be retried")
        await ReportAiService(self.db).enqueue_report_analysis(item.ref_id)
        await self.db.commit()
        return {"retried": 1, "task_ids": [task_id]}

    async def retry_failed_tasks(self) -> dict:
        items = list(await self.db.scalars(select(AiAnalysis).where(AiAnalysis.status == 3)))
        task_ids: list[int] = []
        report_ai = ReportAiService(self.db)
        for item in items:
            if item.type != "report":
                continue
            await report_ai.enqueue_report_analysis(item.ref_id)
            task_ids.append(item.id)
        await self.db.commit()
        return {"retried": len(task_ids), "task_ids": task_ids}

    def _status_label(self, status: int) -> str:
        if status == 1:
            return "RUNNING"
        if status == 2:
            return "COMPLETED"
        if status == 3:
            return "FAILED"
        return "PENDING"

    def _status_value(self, status: str) -> int:
        normalized = status.strip().upper()
        if normalized == "RUNNING":
            return 1
        if normalized == "COMPLETED":
            return 2
        if normalized == "FAILED":
            return 3
        return 0

    def _serialize_task_summary(self, item: AiAnalysis) -> dict:
        duration_ms = None
        if item.started_at and item.completed_at:
            duration_ms = int(
                max(
                    0.0,
                    (item.completed_at - item.started_at).total_seconds() * 1000,
                )
            )

        return {
            "id": item.id,
            "type": item.type,
            "ref_id": item.ref_id,
            "status": self._status_label(item.status),
            "provider": item.provider,
            "model_used": item.model_used,
            "prompt_version": item.prompt_version,
            "prompt_tokens": item.prompt_tokens,
            "output_tokens": item.output_tokens,
            "error_message": item.error_message,
            "content_preview": item.content[:120],
            "created_at": item.created_at,
            "started_at": item.started_at,
            "completed_at": item.completed_at,
            "duration_ms": duration_ms,
        }

    def _build_metric_series(self, items: list[AiAnalysis], *, bucket: str) -> list[dict]:
        grouped: dict[str, dict[str, int]] = {}
        for item in items:
            created_at = self._as_utc(item.created_at)
            if bucket == "month":
                key = created_at.strftime("%Y-%m")
            elif bucket == "week":
                iso_year, iso_week, _ = created_at.isocalendar()
                key = f"{iso_year}-W{iso_week:02d}"
            else:
                key = created_at.strftime("%Y-%m-%d")
            bucket_item = grouped.setdefault(key, {"total": 0, "failed": 0, "completed": 0})
            bucket_item["total"] += 1
            status = self._status_label(item.status)
            if status == "FAILED":
                bucket_item["failed"] += 1
            if status == "COMPLETED":
                bucket_item["completed"] += 1
        return [
            {"bucket": key, **value}
            for key, value in sorted(grouped.items(), key=lambda item: item[0])
        ]

    def _as_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
