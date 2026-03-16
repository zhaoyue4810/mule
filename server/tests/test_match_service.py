from datetime import UTC, datetime

from app.services.match_service import MatchService


def test_as_naive_utc_strips_timezone_info() -> None:
    completed_at = datetime(2026, 3, 16, 10, 45, tzinfo=UTC)

    normalized = MatchService._as_naive_utc(completed_at)

    assert normalized == datetime(2026, 3, 16, 10, 45)
    assert normalized.tzinfo is None
