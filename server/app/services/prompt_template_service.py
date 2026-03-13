from __future__ import annotations

from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.ai import AiPromptTemplate


class PromptTemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        settings = get_settings()
        self.template_path = settings.yaml_config_dir / "ai_prompt_templates.yaml"

    async def ensure_defaults(self) -> None:
        if not self.template_path.exists():
            return

        payload = yaml.safe_load(self.template_path.read_text(encoding="utf-8")) or {}
        templates = payload.get("templates", [])
        changed = False

        for item in templates:
            template_code = str(item["template_code"])
            existing = await self.db.scalar(
                select(AiPromptTemplate).where(
                    AiPromptTemplate.template_code == template_code
                )
            )
            if existing is None:
                existing = AiPromptTemplate(
                    template_code=template_code,
                    scene=str(item["scene"]),
                    system_prompt=str(item["system_prompt"]),
                    user_prompt_tpl=str(item["user_prompt_tpl"]),
                    model_tier=str(item.get("model_tier", "PRO")),
                    temperature=float(item.get("temperature", 0.7)),
                    max_tokens=int(item.get("max_tokens", 1200)),
                    version=int(item.get("version", 1)),
                    is_active=bool(item.get("is_active", True)),
                )
                self.db.add(existing)
                changed = True
                continue

            if int(existing.version) >= int(item.get("version", existing.version)):
                continue

            existing.scene = str(item["scene"])
            existing.system_prompt = str(item["system_prompt"])
            existing.user_prompt_tpl = str(item["user_prompt_tpl"])
            existing.model_tier = str(item.get("model_tier", existing.model_tier))
            existing.temperature = float(item.get("temperature", existing.temperature))
            existing.max_tokens = int(item.get("max_tokens", existing.max_tokens))
            existing.version = int(item.get("version", existing.version))
            existing.is_active = bool(item.get("is_active", existing.is_active))
            changed = True

        if changed:
            await self.db.commit()

    async def get_active_template(self, template_code: str) -> AiPromptTemplate:
        await self.ensure_defaults()
        template = await self.db.scalar(
            select(AiPromptTemplate).where(
                AiPromptTemplate.template_code == template_code,
                AiPromptTemplate.is_active.is_(True),
            )
        )
        if template is None:
            raise LookupError(f"Prompt template not found: {template_code}")
        return template
