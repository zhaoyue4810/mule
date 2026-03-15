from pathlib import Path

from app.services.import_service import ImportService


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_parse_html_demo_preview() -> None:
    service = ImportService()

    preview = service.parse_html_demo(REPO_ROOT / "index.html")

    assert preview.file_type == "html"
    assert preview.summary["test_count"] == 8
    assert "swipe" in preview.summary["interaction_types"]
    assert preview.draft["kind"] == "test_catalog"
    assert len(preview.draft["tests"]) == 8
    assert preview.warnings


def test_parse_docx_outline_preview() -> None:
    service = ImportService()

    preview = service.parse_docx_outline(REPO_ROOT / "xince-design-doc.docx")

    assert preview.file_type == "docx"
    assert preview.summary["heading_count"] >= 1
    assert preview.title
    assert preview.draft["kind"] == "document_outline"


def test_parse_structured_mock_html_preview() -> None:
    service = ImportService()

    preview = service.parse_html_demo(
        REPO_ROOT / "mock" / "imports" / "xince-full-mock-import.html"
    )

    assert preview.file_type == "html"
    assert preview.summary["structured_payload"] is True
    assert preview.summary["test_count"] >= 1
    assert preview.draft["kind"] == "test_catalog"
    first_test = preview.draft["tests"][0]
    assert first_test["dimensions"]
    assert first_test["questions"]
    assert first_test["personas"]
