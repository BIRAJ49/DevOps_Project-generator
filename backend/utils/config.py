from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Project Generator API"
    api_prefix: str = "/api"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/devops_project_generator"
    )
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = 60
    frontend_origins: Annotated[
        list[str], NoDecode
    ] = Field(default_factory=lambda: ["http://localhost:5173"])
    trusted_proxy_ips: Annotated[list[str], NoDecode] = Field(default_factory=list)
    guest_project_limit: int = 3
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 30
    auth_rate_limit_max_requests: int = 10
    rate_limit_max_buckets: int = 10000
    artifact_storage_backend: Literal["local", "s3"] = "local"
    artifact_download_ttl_seconds: int = 900
    archive_directory: Path = BASE_DIR / "generated"
    templates_directory: Path = BASE_DIR / "templates"
    resend_api_key: str | None = None
    email_from: str = "ProjectForge <onboarding@resend.dev>"
    email_verification_code_ttl_minutes: int = 10
    email_verification_resend_cooldown_seconds: int = 60
    email_verification_max_attempts: int = 5
    aws_region: str | None = None
    s3_bucket_name: str | None = None
    s3_artifact_prefix: str = "generated-projects"
    s3_endpoint_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", BASE_DIR / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("frontend_origins", "trusted_proxy_ips", mode="before")
    @classmethod
    def parse_csv_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "aws_region",
        "s3_bucket_name",
        "s3_endpoint_url",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_storage_backend(self) -> "Settings":
        if self.artifact_storage_backend == "s3":
            missing = []
            if not self.aws_region:
                missing.append("AWS_REGION")
            if not self.s3_bucket_name:
                missing.append("S3_BUCKET_NAME")
            if missing:
                raise ValueError(
                    "S3 artifact storage requires these environment variables: "
                    + ", ".join(missing)
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
