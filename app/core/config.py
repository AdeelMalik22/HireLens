from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "HireLens API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    debug: bool = False

    database_url: str = Field(
        default="postgresql+psycopg://myuser:123@localhost:5432/hirelens",
        description="SQLAlchemy database URL.",
    )
    redis_url: str = "redis://localhost:6379/0"
    upload_dir: str = "storage/uploads"
    max_resume_size_mb: int = 10

    openrouter_api_key: str | None = None
    openrouter_model: str = "openrouter/free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout_seconds: float = 60.0
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/integrations/gmail/callback"
    app_secret_key: str = "change-me-in-development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
