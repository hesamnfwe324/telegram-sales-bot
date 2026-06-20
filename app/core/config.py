from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "TelegramAgent"
    APP_ENV: str = "production"
    DEBUG: bool = False
    SECRET_KEY: str
    API_KEY: str

    DATABASE_URL: str
    DATABASE_SSL: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_QUEUE_URL: str = "redis://localhost:6379/1"
    REDIS_CACHE_TTL: int = 3600

    TELEGRAM_API_ID: int = 2040
    TELEGRAM_API_HASH: str = "b18441a1ff607e10a989891a5462e627"

    ADMIN_BOT_TOKEN: str = ""
    ADMIN_TELEGRAM_IDS: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.7

    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── Crypto wallet addresses (set in Render secrets) ──────────────────────
    WALLET_BTC: str = ""
    WALLET_ETH: str = ""
    WALLET_USDT_TRC20: str = ""
    WALLET_USDT_ERC20: str = ""
    WALLET_LTC: str = ""
    WALLET_BNB: str = ""
    WALLET_TRX: str = ""

    SPAM_MAX_MESSAGES_PER_MINUTE: int = 5
    SPAM_MAX_MESSAGES_PER_HOUR: int = 30
    SPAM_SCORE_THRESHOLD: float = 0.8

    ALERT_CPU_THRESHOLD: int = 85
    ALERT_RAM_THRESHOLD: int = 90
    ALERT_DISK_THRESHOLD: int = 90
    HEALTH_CHECK_INTERVAL: int = 60

    POST_DEFAULT_TIMEZONE: str = "Asia/Tehran"
    MAX_CHANNELS_PER_POST: int = 20

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    ALLOWED_HOSTS: str = "*"
    CORS_ORIGINS: str = "*"

    REPLY_TYPING_MIN_DELAY: float = 0.5
    REPLY_TYPING_MAX_DELAY: float = 4.0
    ENABLE_HUMANLIKE_DELAYS: bool = True

    HOT_LEAD_SCORE_THRESHOLD: float = 0.7
    HOT_LEAD_ALERTS_ENABLED: bool = True

    FOLLOWUP_ENABLED: bool = True
    FOLLOWUP_STAGE1_HOURS: int = 24
    FOLLOWUP_STAGE2_HOURS: int = 72
    FOLLOWUP_STAGE3_HOURS: int = 168

    LEARNING_AUTO_APPROVE_THRESHOLD: float = 0.85
    LEARNING_MIN_MESSAGES_FOR_SAMPLE: int = 4

    CONTENT_DEFAULT_LANGUAGES: str = "en,fa"
    CONTENT_HASHTAGS_ENABLED: bool = True

    AI_FACT_EXTRACTION_INTERVAL: int = 10

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
        if v.startswith("postgres://"):
            v = "postgresql" + v[len("postgres"):]
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        parsed = urlparse(v)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        qs.pop("sslmode", None)
        new_query = urlencode({k: vs[0] for k, vs in qs.items()})
        v = urlunparse(parsed._replace(query=new_query))
        return v

    @property
    def admin_ids(self) -> List[int]:
        if not self.ADMIN_TELEGRAM_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_TELEGRAM_IDS.split(",") if x.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def content_default_languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.CONTENT_DEFAULT_LANGUAGES.split(",") if lang.strip()]

    @property
    def active_wallets(self) -> dict:
        """Returns only wallets that have been configured."""
        wallets = {}
        if self.WALLET_BTC:
            wallets["Bitcoin (BTC)"] = self.WALLET_BTC
        if self.WALLET_ETH:
            wallets["Ethereum (ETH)"] = self.WALLET_ETH
        if self.WALLET_USDT_TRC20:
            wallets["USDT (TRC20 / TRON)"] = self.WALLET_USDT_TRC20
        if self.WALLET_USDT_ERC20:
            wallets["USDT (ERC20 / Ethereum)"] = self.WALLET_USDT_ERC20
        if self.WALLET_LTC:
            wallets["Litecoin (LTC)"] = self.WALLET_LTC
        if self.WALLET_BNB:
            wallets["BNB (BEP20 / BSC)"] = self.WALLET_BNB
        if self.WALLET_TRX:
            wallets["TRON (TRX)"] = self.WALLET_TRX
        return wallets


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
