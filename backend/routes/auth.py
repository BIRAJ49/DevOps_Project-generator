from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.security import create_access_token, hash_password, verify_password
from backend.models.database import get_db
from backend.models.entities import User, utcnow
from backend.services.email_verification_service import (
    EmailDeliveryError,
    assign_verification_code,
    can_resend_verification,
    clear_verification_code,
    send_password_reset_email,
    send_verification_email,
    verification_code_matches,
)
from backend.utils.config import get_settings
from backend.utils.rate_limiter import rate_limit
from backend.utils.schemas import (
    AuthResponse,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetVerifyRequest,
    ResendVerificationRequest,
    SignupRequest,
    SignupResponse,
    UserResponse,
    VerifyEmailRequest,
)

router = APIRouter(tags=["auth"])
settings = get_settings()
auth_rate_limit = rate_limit(
    "auth",
    settings.auth_rate_limit_max_requests,
    settings.rate_limit_window_seconds,
    settings.rate_limit_max_buckets,
)


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_rate_limit)],
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> SignupResponse:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        if existing_user.email_verified:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        if not can_resend_verification(existing_user):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another verification code",
            )

        code = assign_verification_code(existing_user)
        try:
            send_verification_email(existing_user.email, code)
        except EmailDeliveryError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        db.commit()
        return SignupResponse(
            email=existing_user.email,
            message="Verification code sent. Check your email to finish signup.",
        )

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    code = assign_verification_code(user)
    db.add(user)

    try:
        send_verification_email(user.email, code)
    except EmailDeliveryError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    db.commit()
    db.refresh(user)

    return SignupResponse(
        email=user.email,
        message="Verification code sent. Check your email to finish signup.",
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
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )

    access_token, expires_at = create_access_token(str(user.id))
    return AuthResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/verify-email",
    response_model=AuthResponse,
    dependencies=[Depends(auth_rate_limit)],
)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    if user.email_verified:
        access_token, expires_at = create_access_token(str(user.id))
        return AuthResponse(
            access_token=access_token,
            expires_at=expires_at,
            user=UserResponse.model_validate(user),
        )
    if (
        user.email_verification_attempts >= settings.email_verification_max_attempts
        or user.email_verification_expires_at is None
        or _code_expired(user)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Request a new code.",
        )

    user.email_verification_attempts += 1
    if not verification_code_matches(user, payload.code):
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    user.email_verified = True
    clear_verification_code(user)
    db.commit()
    db.refresh(user)

    access_token, expires_at = create_access_token(str(user.id))
    return AuthResponse(
        access_token=access_token,
        expires_at=expires_at,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/resend-verification",
    response_model=SignupResponse,
    dependencies=[Depends(auth_rate_limit)],
)
def resend_verification(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> SignupResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or user.email_verified:
        return SignupResponse(
            email=payload.email,
            message="If verification is needed, a new code has been sent.",
        )
    if not can_resend_verification(user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another verification code",
        )

    code = assign_verification_code(user)
    try:
        send_verification_email(user.email, code)
    except EmailDeliveryError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    db.commit()

    return SignupResponse(
        email=user.email,
        message="Verification code sent. Check your email.",
    )


@router.post(
    "/forgot-password",
    response_model=PasswordResetResponse,
    dependencies=[Depends(auth_rate_limit)],
)
def forgot_password(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for this email. Sign up first.",
        )
    if not can_resend_verification(user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another reset code",
        )

    code = assign_verification_code(user)
    try:
        send_password_reset_email(user.email, code)
    except EmailDeliveryError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    db.commit()

    return PasswordResetResponse(
        email=user.email,
        message="Password reset code sent. Check your email.",
    )


@router.post(
    "/verify-reset-code",
    response_model=PasswordResetResponse,
    dependencies=[Depends(auth_rate_limit)],
)
def verify_reset_code(
    payload: PasswordResetVerifyRequest,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    if (
        user.email_verification_attempts >= settings.email_verification_max_attempts
        or user.email_verification_expires_at is None
        or _code_expired(user)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code expired. Request a new code.",
        )

    if not verification_code_matches(user, payload.code):
        user.email_verification_attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    return PasswordResetResponse(
        email=user.email,
        message="Code verified. Choose a new password.",
    )


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
    dependencies=[Depends(auth_rate_limit)],
)
def reset_password(
    payload: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")
    if (
        user.email_verification_attempts >= settings.email_verification_max_attempts
        or user.email_verification_expires_at is None
        or _code_expired(user)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset code expired. Request a new code.",
        )

    user.email_verification_attempts += 1
    if not verification_code_matches(user, payload.code):
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    user.password_hash = hash_password(payload.password)
    user.email_verified = True
    clear_verification_code(user)
    db.commit()

    return PasswordResetResponse(
        email=user.email,
        message="Password reset. Log in with your new password.",
    )


def _code_expired(user: User) -> bool:
    expires_at = user.email_verification_expires_at
    if expires_at is None:
        return True
    now = utcnow()
    if expires_at.tzinfo is None:
        now = now.replace(tzinfo=None)
    return expires_at <= now


@router.get("/me", response_model=UserResponse)
def read_current_user(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
