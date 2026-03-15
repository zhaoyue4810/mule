from datetime import UTC, datetime

from app.services.memory_service import MemoryService


def test_as_naive_utc_strips_timezone_info() -> None:
    created_at = datetime(2026, 3, 15, 10, 30, tzinfo=UTC)

    normalized = MemoryService._as_naive_utc(created_at)

    assert normalized == datetime(2026, 3, 15, 10, 30)
    assert normalized.tzinfo is None
