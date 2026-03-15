from app.services.admin_content_service import AdminContentService


def test_published_timestamp_is_naive_utc() -> None:
    published_at = AdminContentService._published_timestamp()

    assert published_at.tzinfo is None
