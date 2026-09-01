from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app config. Values come from environment variables / .env file.
    Never hardcode secrets here — this class only defines defaults and types.
    """

    debug: bool = False
    api_base_url: str = "http://localhost:8000"
    voice_webhook_secret: str = "mwstesting"

    database_url: str = "postgresql+asyncpg://voiceai:voiceai@db:5432/voiceai"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
