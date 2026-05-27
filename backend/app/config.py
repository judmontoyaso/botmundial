"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Search for .env in backend/ first, then one level up (project root)
_HERE = Path(__file__).resolve().parent.parent  # backend/
_ENV_FILE = _HERE / ".env" if (_HERE / ".env").exists() else _HERE.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # DeepSeek LLM & APIs
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    API_FOOTBALL_KEY: str = ""

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # App
    APP_NAME: str = "ProMundial API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
