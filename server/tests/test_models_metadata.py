from app.core.database import get_metadata


def test_metadata_contains_core_tables() -> None:
    metadata = get_metadata()
    table_names = set(metadata.tables)

    expected = {
        "xc_user",
        "xc_test",
        "xc_test_version",
        "xc_question",
        "xc_option",
        "xc_test_record",
        "xc_report_snapshot",
        "xc_badge_definition",
        "xc_calendar_entry",
        "xc_import_task",
    }

    assert expected.issubset(table_names)


def test_metadata_has_production_schema_scale() -> None:
    metadata = get_metadata()
    assert len(metadata.tables) >= 20
