from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "XinCe API"
    app_env: str = "development"
    app_debug: bool = True

    database_url: str = "postgresql+asyncpg://xince:xince@localhost:5432/xince"
    redis_url: str = "redis://localhost:6379/0"

    wx_appid: str = ""
    wx_secret: str = ""

    sms_provider: str = "mock"
    aliyun_sms_access_key: str = Field(
        default="",
        validation_alias=AliasChoices("ALIYUN_SMS_ACCESS_KEY", "SMS_ACCESS_KEY_ID"),
    )
    aliyun_sms_secret: str = Field(
        default="",
        validation_alias=AliasChoices("ALIYUN_SMS_SECRET", "SMS_ACCESS_KEY_SECRET"),
    )
    aliyun_sms_sign_name: str = Field(
        default="",
        validation_alias=AliasChoices("ALIYUN_SMS_SIGN_NAME", "SMS_SIGN_NAME"),
    )
    aliyun_sms_template_code: str = Field(
        default="",
        validation_alias=AliasChoices("ALIYUN_SMS_TEMPLATE_CODE", "SMS_TEMPLATE_CODE"),
    )
    sms_code_expire_seconds: int = 300
    sms_debug_fixed_code: str = "246810"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    admin_username: str = "admin"
    admin_password_hash: str = "$2y$12$oflUxOU84gxXVSYVVziA1.2D9YxSfiZK5WRNKCiT6gy6N1jM82ZbS"

    dashscope_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("DASHSCOPE_API_KEY", "BAILIAN_API_KEY"),
    )
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_default_model: str = "qwen-max"
    dashscope_lite_model: str = "qwen-plus"

    volc_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("VOLC_API_KEY", "ARK_API_KEY"),
    )
    volc_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volc_default_model: str = "doubao-seed-2-0-lite-260215"
    volc_lite_model: str = "doubao-seed-2-0-lite-260215"
    volc_endpoint_id: str = Field(
        default="",
        validation_alias=AliasChoices("VOLC_ENDPOINT_ID", "ARK_ENDPOINT_ID"),
    )

    oss_endpoint: str = ""
    oss_bucket: str = ""
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""

    yaml_hot_reload: bool = True
    yaml_config_dir: Path = SERVER_DIR / "app" / "config"

    model_config = SettingsConfigDict(
        env_file=SERVER_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
