from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, field_validator


class ProjectType(str, Enum):
    docker = "docker"
    kubernetes = "kubernetes"
    cicd = "cicd"
    terraform = "terraform"


class DifficultyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class ArtifactFormat(str, Enum):
    zip = "zip"
    pdf = "pdf"


class CodeFile(BaseModel):
    path: str
    language: str
    content: str


class GenerateRequest(BaseModel):
    project_type: ProjectType
    difficulty_level: DifficultyLevel


class GenerateResponse(BaseModel):
    generation_id: str
    project_type: ProjectType
    difficulty_level: DifficultyLevel
    idea: str
    why_this_project_matters: str
    architecture: str
    tools: list[str]
    steps: list[str]
    code_files: list[CodeFile]
    readme: str
    download_url: str
    download_zip_url: str
    download_pdf_url: str
    is_authenticated: bool
    guest_requests_remaining: int | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class CredentialsBase(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=72)]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class SignupRequest(CredentialsBase):
    pass


class LoginRequest(CredentialsBase):
    pass


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserResponse
