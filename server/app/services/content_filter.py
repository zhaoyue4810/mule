"""
用户生成内容过滤服务。
基础版：内置敏感词列表匹配。
预留微信内容安全 API 接口。
"""

from __future__ import annotations

import re
from typing import Optional


class ContentFilterError(ValueError):
    """Raised when user text does not pass content moderation."""


_BLOCKED_PATTERNS = [
    r"加[微v]信",
    r"免费领",
    r"点击链接",
    r"自杀",
    r"自残",
]

_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in _BLOCKED_PATTERNS]


class ContentFilterResult:
    def __init__(self, passed: bool, reason: Optional[str] = None):
        self.passed = passed
        self.reason = reason


def check_text(text: str) -> ContentFilterResult:
    """检查文本内容是否通过过滤。"""
    if not text or not text.strip():
        return ContentFilterResult(passed=True)
    for pattern in _compiled:
        if pattern.search(text):
            return ContentFilterResult(passed=False, reason="包含不当内容")
    return ContentFilterResult(passed=True)


async def check_text_wx(text: str, openid: str = "") -> ContentFilterResult:
    """
    预留：调用微信内容安全 API。
    当前降级为本地检查。
    """
    _ = openid
    return check_text(text)
