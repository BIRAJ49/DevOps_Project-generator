from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "DevOps Project Generator API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./devops_project_generator.db"
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    frontend_origins: Annotated[
        list[str], NoDecode
    ] = Field(default_factory=lambda: ["http://localhost:5173"])
    guest_project_limit: int = 3
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 30
    auth_rate_limit_max_requests: int = 10
    archive_directory: Path = BASE_DIR / "generated"
    templates_directory: Path = BASE_DIR / "templates"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("frontend_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
