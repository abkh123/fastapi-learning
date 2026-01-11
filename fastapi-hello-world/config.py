from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "Task API"
    debug: bool = False

    # Database
    database_url: str

    # API
    api_key: str

    # Configuration
    max_tasks_per_user: int = 100
    max_connections: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields in .env
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
