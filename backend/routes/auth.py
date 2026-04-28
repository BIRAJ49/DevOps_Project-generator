from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.security import create_access_token, hash_password, verify_password
from backend.models.database import get_db
from backend.models.entities import User
from backend.utils.config import get_settings
from backend.utils.rate_limiter import rate_limit
from backend.utils.schemas import AuthResponse, LoginRequest, SignupRequest, UserResponse

router = APIRouter(tags=["auth"])
settings = get_settings()
auth_rate_limit = rate_limit(
    "auth", settings.auth_rate_limit_max_requests, settings.rate_limit_window_seconds
)


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_rate_limit)],
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token, expires_at = create_access_token(str(user.id))
    return AuthResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(auth_rate_limit)],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token, expires_at = create_access_token(str(user.id))
    return AuthResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def read_current_user(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)

