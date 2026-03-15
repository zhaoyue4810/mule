"""
短信验证码服务。支持 mock 和阿里云两种模式。
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SmsSender(ABC):
    @abstractmethod
    async def send_code(self, phone: str, code: str) -> bool:
        raise NotImplementedError


class MockSmsSender(SmsSender):
    """开发环境用。验证码打印到日志，不真实发送。"""

    async def send_code(self, phone: str, code: str) -> bool:
        logger.info("[MockSMS] phone=%s, code=%s", phone, code)
        return True


class AliyunSmsSender(SmsSender):
    """阿里云短信服务。需要在 .env 中配置 ALIYUN_SMS_* 系列变量。"""

    def __init__(
        self,
        access_key: str,
        secret: str,
        sign_name: str,
        template_code: str,
    ) -> None:
        self.access_key = access_key
        self.secret = secret
        self.sign_name = sign_name
        self.template_code = template_code

    async def send_code(self, phone: str, code: str) -> bool:
        # 预留实现位置。当前返回 True 模拟成功。
        # 真实接入时使用 alibabacloud-dysmsapi20170525 SDK
        logger.warning(
            "[AliyunSMS] 真实发送未实现，降级为 mock: phone=%s, code=%s",
            phone,
            code,
        )
        return True


def create_sms_sender(provider: str = "mock", **kwargs) -> SmsSender:
    if provider == "aliyun":
        return AliyunSmsSender(**kwargs)
    return MockSmsSender()


def generate_code(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))
