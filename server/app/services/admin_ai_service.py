from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AiAnalysis, AiPromptTemplate
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

    def _as_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
