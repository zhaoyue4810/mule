#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT_DIR / "server" / "app" / "config" / "tests"
OUTPUT_DIR = ROOT_DIR / "mock" / "imports"
OUTPUT_PATH = OUTPUT_DIR / "xince-full-mock-import.html"

GRADIENT_PRESETS = [
    "linear-gradient(135deg,#9B7ED8,#E8729A)",
    "linear-gradient(135deg,#E8729A,#F2A68B)",
    "linear-gradient(135deg,#7CC5B2,#9B7ED8)",
    "linear-gradient(135deg,#D4A853,#F2A68B)",
    "linear-gradient(135deg,#4DA68C,#A8DDD0)",
    "linear-gradient(135deg,#D4894D,#F8C9B5)",
]

PERSONA_EMOJIS = ["✨", "🪐", "🌙", "🌿", "🔥", "🫧", "🌟", "🦊"]


def main() -> None:
    payload = {
        "kind": "test_catalog",
        "source_type": "xince_yaml_mock_bundle",
        "title": "XinCe Full Mock Import Bundle",
        "tests": build_tests(),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_html(payload), encoding="utf-8")
    print(f"[ok] generated {OUTPUT_PATH}")


def build_tests() -> list[dict]:
    tests: list[dict] = []
    for index, path in enumerate(sorted(TESTS_DIR.glob("*.yaml")), start=1):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        test_code = data["test_code"]
        duration_hint = (
            f'{data.get("duration_minutes")}分钟'
            if data.get("duration_minutes")
            else "8分钟"
        )
        tests.append(
            {
                "test_code": test_code,
                "name": data["name"],
                "category": data["category"],
                "description": data.get("description")
                or f'{data["name"]} 的联调导入样本。',
                "duration_hint": duration_hint,
                "is_match_enabled": bool(
                    data.get("is_match", test_code in {"bff", "couple"})
                ),
                "participant_count": 12000 + index * 1876,
                "sort_order": index,
                "cover_gradient": GRADIENT_PRESETS[(index - 1) % len(GRADIENT_PRESETS)],
                "report_template_code": f"{test_code}_mock_v1",
                "dimensions": build_dimensions(data),
                "questions": build_questions(data),
                "personas": build_personas(data, index),
            }
        )
    return tests


def build_dimensions(data: dict) -> list[dict]:
    dimensions = data.get("dimensions") or []
    return [
        {
            "dim_code": item["code"],
            "dim_name": item["name"],
            "max_score": 100,
            "sort_order": index,
        }
        for index, item in enumerate(dimensions, start=1)
    ]


def build_questions(data: dict) -> list[dict]:
    questions = []
    for item in data.get("questions") or []:
        question = {
            "question_code": item.get("code"),
            "seq": item["seq"],
            "question_text": item["title"],
            "interaction_type": item["interaction_type"],
            "emoji": item.get("emoji"),
            "config": build_question_config(item),
            "dim_weights": item.get("dimension_weights") or {},
            "options": [],
        }

        for option_index, option in enumerate(item.get("options") or [], start=1):
            question["options"].append(
                {
                    "option_code": option.get("code"),
                    "seq": option_index,
                    "label": option["text"],
                    "emoji": option.get("emoji"),
                    "value": float(option.get("value", 0)),
                    "score_rules": (
                        {
                            "dimension_code": option["dimension_code"],
                            "value": float(option.get("value", 0)),
                        }
                        if option.get("dimension_code")
                        else None
                    ),
                    "ext_config": None,
                }
            )

        questions.append(question)

    return questions


def build_question_config(item: dict) -> dict | None:
    config_keys = [
        "scene",
        "tip",
        "labels",
        "words",
        "axisX",
        "axisY",
        "min",
        "max",
        "left_label",
        "right_label",
    ]
    config = {key: item[key] for key in config_keys if key in item}
    return config or None


def build_personas(data: dict, seed: int) -> list[dict]:
    personas = []
    for index, item in enumerate(data.get("personas") or [], start=1):
        personas.append(
            {
                "persona_key": item["code"],
                "persona_name": item["name"],
                "emoji": PERSONA_EMOJIS[(seed + index - 2) % len(PERSONA_EMOJIS)],
                "rarity_percent": max(8, 100 - index * 13),
                "description": f'{item["name"]} 是 {data["name"]} 的导入联调人格样本。',
                "soul_signature": f'在 {data["category"]} 场景里，{item["name"]} 往往会表现出稳定而鲜明的偏好。',
                "keywords": [data["category"], "联调样本", item["name"]],
                "dim_pattern": item.get("dim_pattern") or {},
                "capsule_prompt": f'如果未来的你再次看到「{item["name"]}」这一面，最想提醒今天的自己什么？',
            }
        )
    return personas


def build_html(payload: dict) -> str:
    pretty_json = json.dumps(payload, ensure_ascii=False, indent=2)
    title = payload["title"]
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <style>
      body {{
        margin: 0;
        font-family: "PingFang SC", "Helvetica Neue", sans-serif;
        background: linear-gradient(180deg, #fffaf6 0%, #f5efe6 100%);
        color: #3f3027;
      }}
      main {{
        max-width: 880px;
        margin: 0 auto;
        padding: 48px 24px 72px;
      }}
      h1 {{
        margin: 0 0 12px;
        font-size: 34px;
      }}
      p {{
        line-height: 1.7;
        color: #6f6158;
      }}
      .card {{
        margin-top: 24px;
        padding: 20px 24px;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.88);
        box-shadow: 0 16px 40px rgba(140, 103, 78, 0.08);
      }}
      code {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        background: #f1e4d7;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>{title}</h1>
      <p>这是一份给心测后台“内容导入”页面使用的完整 mock 导入包。</p>
      <div class="card">
        <p>使用方式：</p>
        <p>1. 启动 <code>./scripts/dev_stack.sh up</code></p>
        <p>2. 进入后台“内容导入”上传本文件</p>
        <p>3. 通过导入后，去“测试管理”发布你要给 H5 看的版本</p>
      </div>
    </main>
    <script id="xince-mock-import" type="application/json">
{pretty_json}
    </script>
  </body>
</html>
"""


if __name__ == "__main__":
    main()
