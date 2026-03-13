from __future__ import annotations

import logging
import random
from pathlib import Path
from threading import RLock
from typing import Any

import yaml

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class YamlConfigStore:
    def __init__(self, config_dir: Path | None = None) -> None:
        settings = get_settings()
        self.config_dir = Path(config_dir or settings.yaml_config_dir)
        self._store: dict[str, Any] = {}
        self._loaded = False
        self._lock = RLock()

    def load_all(self) -> None:
        with self._lock:
            self._store = {
                "interaction_types": self._load_file("interaction_types.yaml"),
                "tests": {},
                "prompts": {},
                "badges": self._load_file("badges.yaml"),
                "soul_fragments": self._load_file("soul_fragments.yaml"),
                "daily_questions": self._load_file("daily_questions.yaml"),
            }

            tests_dir = self.config_dir / "tests"
            if tests_dir.exists():
                for path in sorted(tests_dir.glob("*.yaml")):
                    data = self._load_file(f"tests/{path.name}")
                    test_code = data.get("test_code")
                    if test_code:
                        self._store["tests"][test_code] = data

            prompts_dir = self.config_dir / "prompts"
            if prompts_dir.exists():
                for path in sorted(prompts_dir.glob("*.yaml")):
                    self._store["prompts"][path.stem] = self._load_file(
                        f"prompts/{path.name}"
                    )

            self._loaded = True
            logger.info(
                "Loaded YAML config: %s tests, %s interaction types",
                len(self._store["tests"]),
                len(self.get_interaction_types()),
            )

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_all()

    def reload(self) -> None:
        self.load_all()

    def _load_file(self, relative_path: str) -> dict[str, Any]:
        path = self.config_dir / relative_path
        if not path.exists():
            return {}

        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def get_interaction_types(self) -> dict[str, dict[str, Any]]:
        self.ensure_loaded()
        return self._store.get("interaction_types", {}).get("interaction_types", {})

    def get_all_tests(self) -> dict[str, dict[str, Any]]:
        self.ensure_loaded()
        return self._store.get("tests", {})

    def get_test(self, test_code: str) -> dict[str, Any] | None:
        self.ensure_loaded()
        return self._store.get("tests", {}).get(test_code)

    def get_prompt(self, prompt_key: str) -> dict[str, Any]:
        self.ensure_loaded()
        return self._store.get("prompts", {}).get(prompt_key, {})

    def get_micro_feedback(self, interaction_type: str, value: Any = None) -> str:
        self.ensure_loaded()
        micro_feedback = self.get_prompt("micro_feedback")
        by_type = micro_feedback.get("by_interaction_type", {})
        fallback = by_type.get("default", ["继续加油~"])

        pool: list[str] | dict[str, list[str]] = by_type.get(interaction_type, fallback)

        if isinstance(pool, dict):
            if interaction_type == "swipe":
                key = "right" if value in {"right", 1, 1.0, True} else "left"
                pool = pool.get(key, fallback)
            elif interaction_type == "slider":
                if value is not None and float(value) <= 0.33:
                    pool = pool.get("low", fallback)
                elif value is not None and float(value) >= 0.67:
                    pool = pool.get("high", fallback)
                else:
                    pool = pool.get("mid", fallback)
            else:
                pool = next(iter(pool.values()), fallback)

        return random.choice(pool or fallback)

    def summary(self) -> dict[str, int]:
        self.ensure_loaded()
        return {
            "interaction_type_count": len(self.get_interaction_types()),
            "test_count": len(self.get_all_tests()),
            "prompt_group_count": len(self._store.get("prompts", {})),
            "badge_count": len(self._store.get("badges", {}).get("badges", [])),
            "soul_fragment_category_count": len(
                self._store.get("soul_fragments", {}).get("categories", [])
            ),
            "daily_question_count": len(
                self._store.get("daily_questions", {}).get("questions", [])
            ),
        }


yaml_config = YamlConfigStore()
