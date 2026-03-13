from __future__ import annotations

import argparse
import asyncio
import json
from decimal import Decimal

from app.models.ai import AiPromptTemplate
from app.services.ai_gateway import AiGateway


def _build_template(provider: str) -> AiPromptTemplate:
    return AiPromptTemplate(
        template_code=f"{provider}_smoke",
        scene="report",
        system_prompt="你是一个测试助手，请简洁回答。",
        user_prompt_tpl="请用一句中文确认 {provider} 通道可用，并提到关键词：{keyword}",
        model_tier="LITE",
        temperature=Decimal("0.10"),
        max_tokens=120,
        version=1,
        is_active=True,
    )


async def _run(provider: str) -> dict:
    gateway = AiGateway()
    template = _build_template(provider)
    context = {"provider": provider, "keyword": "xince-smoke"}
    fallback = f"{provider} fallback success: xince-smoke"

    if provider == "dashscope":
        original_volc_key = gateway.settings.volc_api_key
        gateway.settings.volc_api_key = ""
        try:
            return await gateway.generate_from_template(template, context, fallback)
        finally:
            gateway.settings.volc_api_key = original_volc_key

    if provider == "volc":
        original_dashscope_key = gateway.settings.dashscope_api_key
        gateway.settings.dashscope_api_key = ""
        try:
            return await gateway.generate_from_template(template, context, fallback)
        finally:
            gateway.settings.dashscope_api_key = original_dashscope_key

    raise ValueError(f"Unsupported provider: {provider}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test AI provider connectivity.")
    parser.add_argument("--provider", choices=["dashscope", "volc"], required=True)
    args = parser.parse_args()

    result = asyncio.run(_run(args.provider))
    print(
        json.dumps(
            {
                "provider": result.get("provider"),
                "model_used": result.get("model_used"),
                "prompt_version": result.get("prompt_version"),
                "content_preview": str(result.get("content", ""))[:160],
                "prompt_tokens": result.get("prompt_tokens"),
                "output_tokens": result.get("output_tokens"),
                "provider_errors": result.get("provider_errors", []),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
