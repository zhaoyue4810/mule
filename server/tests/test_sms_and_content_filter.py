from app.services.content_filter import check_text
from app.services.sms_service import MockSmsSender, create_sms_sender, generate_code


def test_sms_sender_factory_returns_mock_by_default() -> None:
    sender = create_sms_sender()
    assert isinstance(sender, MockSmsSender)


def test_generate_code_returns_expected_length() -> None:
    code = generate_code()
    assert len(code) == 6
    assert code.isdigit()


def test_content_filter_blocks_sensitive_text() -> None:
    result = check_text("欢迎点击链接免费领礼包")
    assert result.passed is False
    assert result.reason == "包含不当内容"


def test_content_filter_allows_normal_text() -> None:
    result = check_text("喜欢观察自己和别人。")
    assert result.passed is True
    assert result.reason is None
