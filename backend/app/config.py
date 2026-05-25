"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # DeepSeek LLM & APIs
    DEEPSEEK_API_KEY: str = ""
    API_FOOTBALL_KEY: str = ""

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # App
    APP_NAME: str = "BotMundial API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
