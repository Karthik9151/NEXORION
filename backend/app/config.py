"""Environment-backed settings and production configuration guards."""

from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./nexorion.db"
    session_ttl_hours: int = Field(default=12, ge=1, le=168)
    session_cookie_secure: bool = False
    session_cookie_name: str = "nexorion_session"
    csrf_cookie_name: str = "nexorion_csrf"
    allow_self_registration: bool = True

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env == "production":
            if not self.database_url.startswith("postgresql+psycopg://"):
                raise ValueError(
                    "Production requires a postgresql+psycopg:// URL; "
                    "SQLite is for local development/tests only."
                )
            if not self.session_cookie_secure:
                raise ValueError("SESSION_COOKIE_SECURE must be true in production.")
            if self.allow_self_registration:
                raise ValueError(
                    "Self-registration must be disabled in production until "
                    "an approved onboarding flow exists."
                )
        return self


def get_settings() -> Settings:
    """Load validated settings from environment and the optional local .env file."""
    return Settings()
