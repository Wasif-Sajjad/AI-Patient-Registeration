import os
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_db_url(url: str) -> str:
    if not url:
        raise ValueError(
            "DATABASE_URL is empty or unset. Check your Railway variable reference."
        )
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    """Central app config. Values come from environment variables / .env file.
    Never hardcode secrets here — this class only defines defaults and types.
    """

    debug: bool = False
    api_base_url: str = "http://localhost:8000"
    voice_webhook_secret: str = "mwstesting"
    allowed_origins: str = "*"

    database_url: str = _normalize_db_url(
        os.getenv("DATABASE_URL", "postgresql+asyncpg://voiceai:voiceai@db:5432/voiceai")
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
