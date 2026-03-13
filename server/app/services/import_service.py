from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup
from docx import Document


@dataclass
class ImportPreview:
    file_type: str
    title: str
    summary: dict
    draft: dict
    warnings: list[str]


class ImportService:
    def parse_html_demo(self, html_path: str | Path) -> ImportPreview:
        path = Path(html_path)
        source = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(source, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else path.name
        tests_block = self._extract_js_array(source, "T")
        tests = re.findall(r"id:'([^']+)',name:'([^']+)'", tests_block)
        interaction_types = sorted(set(re.findall(r"tp:'([^']+)'", source)))
        local_storage_keys = sorted(set(re.findall(r"xc_[a-z_]+", source)))
        tests_with_meta = re.findall(
            r"id:'([^']+)',name:'([^']+)'.*?cat:'([^']+)'.*?dur:'([^']+)'.*?cnt:'([^']+)'",
            tests_block,
            re.S,
        )

        summary = {
            "page_title": title,
            "test_count": len(tests),
            "tests": [{"code": code, "name": name} for code, name in tests],
            "interaction_types": interaction_types,
            "local_storage_keys": local_storage_keys,
        }
        draft = {
            "kind": "test_catalog",
            "source_type": "html_demo",
            "title": title,
            "tests": [
                {
                    "test_code": code,
                    "name": name,
                    "category": category,
                    "duration_hint": duration,
                    "participant_count_text": participant_count,
                }
                for code, name, category, duration, participant_count in tests_with_meta
            ],
        }
        warnings = [
            "HTML preview is suitable for draft extraction, not direct publishing.",
            "Question-level content still needs structured import before editing and publishing.",
        ]
        return ImportPreview(
            file_type="html",
            title=title,
            summary=summary,
            draft=draft,
            warnings=warnings,
        )

    def parse_docx_outline(self, docx_path: str | Path) -> ImportPreview:
        path = Path(docx_path)
        document = Document(path)

        headings: list[dict[str, str]] = []
        paragraphs: list[str] = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            style_name = paragraph.style.name if paragraph.style else ""
            if style_name.startswith("Heading"):
                headings.append({"style": style_name, "text": text})
            else:
                paragraphs.append(text)

        title = headings[0]["text"] if headings else path.stem
        summary = {
            "heading_count": len(headings),
            "headings": headings[:20],
            "paragraph_count": len(paragraphs),
            "sample_paragraphs": paragraphs[:10],
        }
        draft = {
            "kind": "document_outline",
            "source_type": "docx",
            "title": title,
            "sections": headings[:20],
            "content_excerpt": paragraphs[:10],
        }
        warnings = [
            "DOCX preview currently extracts outline only.",
            "Structured test conversion still requires rule mapping before draft editing and publishing.",
        ]
        return ImportPreview(
            file_type="docx",
            title=title,
            summary=summary,
            draft=draft,
            warnings=warnings,
        )

    def _extract_js_array(self, source: str, const_name: str) -> str:
        marker = f"const {const_name}="
        start = source.find(marker)
        if start == -1:
            return ""

        start = source.find("[", start)
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
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return source[start : index + 1]

        return ""
