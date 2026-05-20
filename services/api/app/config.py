"""集中配置 · 从 .env.local 读取所有环境变量."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[REPO_ROOT / ".env.local", REPO_ROOT / ".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 基础
    APP_NAME: str = "video-ct"
    NODE_ENV: str = "development"
    LOG_LEVEL: str = "info"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_BASE_URL: str = "http://localhost:8000"

    # JWT
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/video_ct.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI · DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL_CHAT: str = "deepseek-chat"
    DEEPSEEK_MODEL_PRO: str = "deepseek-reasoner"

    # AI · 硅基流动
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL_EMBEDDING: str = "BAAI/bge-large-zh-v1.5"
    SILICONFLOW_MODEL_RERANK: str = "BAAI/bge-reranker-v2-m3"
    SILICONFLOW_MODEL_VISION: str = "Qwen/Qwen2-VL-72B-Instruct"
    SILICONFLOW_MODEL_LLM_FALLBACK: str = "Qwen/Qwen2.5-72B-Instruct"

    # 微信（mock 占位）
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_PAY_MCH_ID: str = ""
    WECHAT_PAY_API_KEY: str = ""

    # 平台 OAuth（mock 占位）
    DOUYIN_CLIENT_KEY: str = ""
    DOUYIN_CLIENT_SECRET: str = ""

    # 短信（mock 占位）
    ALIYUN_SMS_ACCESS_KEY: str = ""
    ALIYUN_SMS_ACCESS_SECRET: str = ""
    ALIYUN_SMS_SIGN_NAME: str = "视频CT"
    ALIYUN_SMS_TEMPLATE_OTP: str = ""

    # 存储
    OSS_ENDPOINT: str = "local"
    OSS_ACCESS_KEY: str = ""
    OSS_SECRET_KEY: str = ""
    OSS_BUCKET: str = "video-ct-dev"
    OSS_REGION: str = "cn-hangzhou"
    STORAGE_LOCAL_PATH: str = "./storage/uploads"

    # 业务参数（来自战略文档）
    FREE_MONTHLY_SCANS: int = 3
    PRO_PRICE_CNY: int = 99
    MAX_PRICE_CNY: int = 499
    SINGLE_SCAN_PRICE_CNY: int = 19
    REFERRER_REWARD_CNY: int = 18
    REFERRER_DEDUCT_THRESHOLD: int = 99

    # 风控
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_UPLOAD_SIZE_MB: int = 200

    # 计算属性
    @property
    def is_production(self) -> bool:
        return self.NODE_ENV == "production"

    @property
    def database_sync_url(self) -> str:
        """同步版本 URL · 用于 Alembic 迁移."""
        return self.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
