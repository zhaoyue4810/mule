#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a structured inventory from the XinCe HTML demo."
    )
    parser.add_argument("--html", type=Path, default=Path("index.html"))
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def extract_js_array(source: str, const_name: str) -> str:
    marker = f"const {const_name}="
    start = source.find(marker)
    if start == -1:
        raise ValueError(f"Cannot find {marker!r}")

    start = source.find("[", start)
    if start == -1:
        raise ValueError(f"Cannot find array start for {const_name!r}")

    depth = 0
    in_string: str | None = None
    escaped = False

    for index in range(start, len(source)):
        char = source[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
            continue

        if char in {"'", '"'}:
            in_string = char
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]

    raise ValueError(f"Unbalanced array for {const_name!r}")


def split_top_level_objects(array_source: str) -> list[str]:
    objects: list[str] = []
    depth = 0
    in_string: str | None = None
    escaped = False
    object_start: int | None = None

    for index, char in enumerate(array_source):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
            continue

        if char in {"'", '"'}:
            in_string = char
            continue

        if char == "{":
            if depth == 0:
                object_start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and object_start is not None:
                objects.append(array_source[object_start : index + 1])
                object_start = None

    return objects


def extract_bracket_block(source: str, marker: str, opener: str, closer: str) -> str:
    start = source.find(marker)
    if start == -1:
        return ""

    start = source.find(opener, start)
    if start == -1:
        return ""

    depth = 0
    in_string: str | None = None
    escaped = False

    for index in range(start, len(source)):
        char = source[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == in_string:
                in_string = None
            continue

        if char in {"'", '"'}:
            in_string = char
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return source[start : index + 1]

    return ""


def extract_field(source: str, field_name: str) -> str:
    pattern = re.compile(rf"{field_name}:'([^']*)'")
    match = pattern.search(source)
    return match.group(1) if match else ""


def extract_list_items(list_source: str) -> list[str]:
    return re.findall(r"'([^']+)'", list_source)


def build_inventory(html_path: Path) -> dict[str, object]:
    source = html_path.read_text(encoding="utf-8")
    tests_array = extract_js_array(source, "T")
    test_blocks = split_top_level_objects(tests_array)

    tests: list[dict[str, object]] = []
    interaction_usage: Counter[str] = Counter()

    for block in test_blocks:
        questions_block = extract_bracket_block(block, "qs:", "[", "]")
        dims_block = extract_bracket_block(block, "dims:", "[", "]")
        question_types = re.findall(r"tp:'([^']+)'", questions_block)

        interaction_usage.update(question_types)

        tests.append(
            {
                "id": extract_field(block, "id"),
                "name": extract_field(block, "name"),
                "category": extract_field(block, "cat"),
                "duration": extract_field(block, "dur"),
                "participants": extract_field(block, "cnt"),
                "is_match": "isMatch:true" in block,
                "question_count": len(re.findall(r"\{t:'", questions_block)),
                "dimension_count": len(extract_list_items(dims_block)),
                "question_types": dict(Counter(question_types)),
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(html_path),
        "test_count": len(tests),
        "match_test_count": sum(1 for item in tests if item["is_match"]),
        "interaction_type_count": len(interaction_usage),
        "interaction_type_usage": dict(sorted(interaction_usage.items())),
        "tests": tests,
    }


def main() -> int:
    args = parse_args()
    inventory = build_inventory(args.html)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(json.dumps(inventory, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
