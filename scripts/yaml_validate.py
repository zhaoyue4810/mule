#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = REPO_ROOT / "server"

sys.path.insert(0, str(SERVER_DIR))

from app.core.yaml_loader import YamlConfigStore  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate XinCe YAML config files.")
    parser.add_argument("--test", help="Validate only one test_code.")
    return parser.parse_args()


def validate_test(test_code: str, data: dict, interaction_types: set[str]) -> list[str]:
    errors: list[str] = []

    dimensions = data.get("dimensions", [])
    dimension_codes = [item.get("code") for item in dimensions if item.get("code")]

    if not dimension_codes:
        errors.append(f"{test_code}: missing dimensions")
    elif len(dimension_codes) != len(set(dimension_codes)):
        errors.append(f"{test_code}: duplicate dimension codes")

    questions = data.get("questions", [])
    if not questions:
        errors.append(f"{test_code}: missing questions")

    seq_seen: set[int] = set()

    for question in questions:
        seq = question.get("seq")
        if seq is None:
            errors.append(f"{test_code}: question without seq")
        elif seq in seq_seen:
            errors.append(f"{test_code}: duplicated seq {seq}")
        else:
            seq_seen.add(seq)

        interaction_type = question.get("interaction_type")
        if interaction_type not in interaction_types:
            errors.append(
                f"{test_code}: question {question.get('code', seq)} uses unknown "
                f"interaction_type {interaction_type!r}"
            )

        options = question.get("options", [])
        weights = question.get("dimension_weights", {})

        if not options and not weights:
            errors.append(
                f"{test_code}: question {question.get('code', seq)} needs options "
                "or dimension_weights"
            )

        for option in options:
            dimension_code = option.get("dimension_code")
            if dimension_code not in dimension_codes:
                errors.append(
                    f"{test_code}: option {option.get('code')} references "
                    f"unknown dimension {dimension_code!r}"
                )

            value = option.get("value")
            if value is None:
                errors.append(
                    f"{test_code}: option {option.get('code')} is missing value"
                )
                continue

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                errors.append(
                    f"{test_code}: option {option.get('code')} value is not numeric"
                )
                continue

            if not 0 <= numeric_value <= 1:
                errors.append(
                    f"{test_code}: option {option.get('code')} value {numeric_value} "
                    "must be in [0, 1]"
                )

        for dimension_code, weight in weights.items():
            if dimension_code not in dimension_codes:
                errors.append(
                    f"{test_code}: question {question.get('code', seq)} weight "
                    f"references unknown dimension {dimension_code!r}"
                )

            try:
                float(weight)
            except (TypeError, ValueError):
                errors.append(
                    f"{test_code}: question {question.get('code', seq)} weight "
                    f"{dimension_code!r} is not numeric"
                )

    personas = data.get("personas", [])
    if not personas:
        errors.append(f"{test_code}: missing personas")

    for persona in personas:
        pattern = persona.get("dim_pattern", {})
        if not pattern:
            errors.append(
                f"{test_code}: persona {persona.get('code')} missing dim_pattern"
            )
            continue

        for dimension_code, value in pattern.items():
            if dimension_code not in dimension_codes:
                errors.append(
                    f"{test_code}: persona {persona.get('code')} references "
                    f"unknown dimension {dimension_code!r}"
                )

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                errors.append(
                    f"{test_code}: persona {persona.get('code')} value "
                    f"for {dimension_code!r} is not numeric"
                )
                continue

            if not 0 <= numeric_value <= 1:
                errors.append(
                    f"{test_code}: persona {persona.get('code')} value "
                    f"{numeric_value} must be in [0, 1]"
                )

    return errors


def main() -> int:
    args = parse_args()
    store = YamlConfigStore(SERVER_DIR / "app" / "config")
    store.load_all()

    interaction_types = set(store.get_interaction_types())
    all_tests = store.get_all_tests()

    if args.test:
        all_tests = {
            code: data for code, data in all_tests.items() if code == args.test
        }
        if not all_tests:
            print(f"[ERROR] test_code {args.test!r} not found")
            return 1

    errors: list[str] = []
    for test_code, data in all_tests.items():
        errors.extend(validate_test(test_code, data, interaction_types))

    if errors:
        print("[ERROR] YAML validation failed:")
        for item in errors:
            print(f" - {item}")
        return 1

    print(
        "[OK] YAML validation passed: "
        f"{len(interaction_types)} interaction types, {len(all_tests)} tests"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
