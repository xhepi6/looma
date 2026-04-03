from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_env: str = "dev"
    app_secret_key: str = "change-me-in-production-use-secure-random-key"
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Discord notifications (optional)
    discord_webhook_url: Optional[str] = None

    # ntfy notifications (optional)
    ntfy_username: Optional[str] = None
    ntfy_password: Optional[str] = None
    reminder_enabled: bool = False
    reminder_interval_minutes: int = 10
    reminder_due_soon_hours: int = 24

    # Seed users
    seed_admin_users: bool = True
    seed_user_1_username: str = "alice"
    seed_user_1_password: str = "password123"
    seed_user_2_username: str = "bob"
    seed_user_2_password: str = "password123"

    # Translation (OpenRouter)
    openrouter_api_key: Optional[str] = None
    translation_model: str = "google/gemini-2.0-flash-001"
    translation_enabled: bool = True

    # Chat agent (PydanticAI + OpenRouter)
    chat_model: str = "google/gemini-2.0-flash-001"
    chat_enabled: bool = True
    chat_rate_limit: int = 20

    # TMDB metadata enrichment (optional)
    tmdb_api_key: Optional[str] = None
    tmdb_enabled: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
