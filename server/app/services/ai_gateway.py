from __future__ import annotations

from string import Formatter

import httpx

from app.core.config import get_settings
from app.models.ai import AiPromptTemplate


class SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


class AiGateway:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_from_template(
        self,
        template: AiPromptTemplate,
        context: dict[str, object],
        fallback_text: str,
    ) -> dict:
        prompt = self._render_prompt(template.user_prompt_tpl, context)
        provider_errors: list[str] = []

        if self.settings.dashscope_api_key:
            try:
                return await self._chat_completion(
                    provider="dashscope",
                    api_key=self.settings.dashscope_api_key,
                    base_url=self.settings.dashscope_base_url,
                    model=(
                        self.settings.dashscope_default_model
                        if template.model_tier.upper() == "PRO"
                        else self.settings.dashscope_lite_model
                    ),
                    system_prompt=template.system_prompt,
                    user_prompt=prompt,
                    temperature=float(template.temperature),
                    max_tokens=int(template.max_tokens),
                    prompt_version=str(template.version),
                )
            except Exception as exc:
                provider_errors.append(f"dashscope: {exc}")

        if self.settings.volc_api_key:
            try:
                return await self._chat_completion(
                    provider="volc",
                    api_key=self.settings.volc_api_key,
                    base_url=self.settings.volc_base_url,
                    model=(
                        self.settings.volc_endpoint_id
                        or self.settings.volc_default_model
                        if template.model_tier.upper() == "PRO"
                        else self.settings.volc_endpoint_id or self.settings.volc_lite_model
                    ),
                    system_prompt=template.system_prompt,
                    user_prompt=prompt,
                    temperature=float(template.temperature),
                    max_tokens=int(template.max_tokens),
                    prompt_version=str(template.version),
                )
            except Exception as exc:
                provider_errors.append(f"volc: {exc}")

        return {
            "provider": "fallback",
            "model_used": "local-template-v1",
            "prompt_version": str(template.version),
            "prompt_tokens": len(prompt),
            "output_tokens": len(fallback_text),
            "content": fallback_text,
            "provider_errors": provider_errors,
        }

    def _render_prompt(self, prompt_template: str, context: dict[str, object]) -> str:
        formatter = Formatter()
        field_names = [
            field_name
            for _, field_name, _, _ in formatter.parse(prompt_template)
            if field_name
        ]
        safe_context = SafeFormatDict(
            {field_name: str(context.get(field_name, "")) for field_name in field_names}
        )
        return prompt_template.format_map(safe_context)

    async def _chat_completion(
        self,
        *,
        provider: str,
        api_key: str,
        base_url: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        prompt_version: str,
    ) -> dict:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            payload = response.json()

        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        usage = payload.get("usage", {})
        return {
            "provider": provider,
            "model_used": model,
            "prompt_version": prompt_version,
            "prompt_tokens": usage.get("prompt_tokens"),
            "output_tokens": usage.get("completion_tokens"),
            "content": content,
        }
