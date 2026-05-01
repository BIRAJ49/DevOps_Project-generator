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


class SuggestRequest(BaseModel):
    prompt: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]


class Suggestion(BaseModel):
    category: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
    difficulty_level: DifficultyLevel
    title: str
    rationale: str


class SuggestResponse(BaseModel):
    suggestions: list[Suggestion]
    is_authenticated: bool = False
    guest_requests_remaining: int | None = None


class ProjectDetailsRequest(BaseModel):
    prompt: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]
    suggestion: Suggestion


class ProjectDetailsResponse(BaseModel):
    title: str
    category: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
    difficulty_level: DifficultyLevel
    rationale: str
    overview: str
    architecture: list[str]
    recommended_tools: list[str]
    implementation_steps: list[str]
    deliverables: list[str]
    risks: list[str]
    is_authenticated: bool = False
    guest_requests_remaining: int | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    email_verified: bool
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


class SignupResponse(BaseModel):
    email: EmailStr
    requires_verification: bool = True
    message: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=6, max_length=6)]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ResendVerificationRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class PasswordResetRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=6, max_length=6)]
    password: Annotated[str, StringConstraints(min_length=8, max_length=72)]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class PasswordResetResponse(BaseModel):
    email: EmailStr
    message: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserResponse
