from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Code Review Assistant"

    # Database (async driver is required)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/code_review"

    # Auth
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # GenAI
    llm_provider: str = "anthropic"  # "anthropic" or "mock"
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    llm_max_tokens: int = 2000
    llm_timeout_seconds: float = 60.0

    # Limits
    max_code_chars: int = 20_000


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
