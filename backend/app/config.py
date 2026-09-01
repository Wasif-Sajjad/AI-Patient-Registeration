import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app config. Values come from environment variables / .env file.
    Never hardcode secrets here — this class only defines defaults and types.
    """

    debug: bool = False
    api_base_url: str = "http://localhost:8000"
    voice_webhook_secret: str = "mwstesting"
    allowed_origins: str = "*"

    database_url: str = "postgresql+asyncpg://voiceai:voiceai@db:5432/voiceai"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "DATABASE_URL is empty or unset. Check your Railway variable reference."
            )
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
