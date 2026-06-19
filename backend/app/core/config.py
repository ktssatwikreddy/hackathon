from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Training Attendance & Performance Management System"
    environment: str = "local"

    # SQLite by default (zero-install). Swap one line to move to MySQL/Postgres.
    database_url: str = "sqlite:///./tapms.db"

    # Auth / JWT
    jwt_secret_key: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # QR attendance
    attendance_token_ttl_minutes: int = 15
    frontend_base_url: str = "http://localhost:5173"

    # AI
    mock_ai: bool = True
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # Seed control (Docker entrypoint)
    seed: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
