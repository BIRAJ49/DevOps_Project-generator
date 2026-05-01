from datetime import timedelta
from hashlib import sha256
import hmac
import secrets

import httpx
from fastapi import HTTPException, status

from backend.models.entities import User, utcnow
from backend.utils.config import get_settings

settings = get_settings()


class EmailDeliveryError(RuntimeError):
    pass


def _verification_code_hash(email: str, code: str) -> str:
    message = f"{email.strip().lower()}:{code}".encode("utf-8")
    secret = settings.jwt_secret_key.encode("utf-8")
    return hmac.new(secret, message, sha256).hexdigest()


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def verification_code_matches(user: User, code: str) -> bool:
    if not user.email_verification_code_hash:
        return False
    expected_hash = _verification_code_hash(user.email, code)
    return hmac.compare_digest(user.email_verification_code_hash, expected_hash)


def assign_verification_code(user: User) -> str:
    code = _generate_code()
    now = utcnow()
    user.email_verification_code_hash = _verification_code_hash(user.email, code)
    user.email_verification_expires_at = now + timedelta(
        minutes=settings.email_verification_code_ttl_minutes
    )
    user.email_verification_sent_at = now
    user.email_verification_attempts = 0
    return code


def clear_verification_code(user: User) -> None:
    user.email_verification_code_hash = None
    user.email_verification_expires_at = None
    user.email_verification_sent_at = None
    user.email_verification_attempts = 0


def can_resend_verification(user: User) -> bool:
    if user.email_verification_sent_at is None:
        return True
    cooldown_ends_at = user.email_verification_sent_at + timedelta(
        seconds=settings.email_verification_resend_cooldown_seconds
    )
    now = utcnow()
    if cooldown_ends_at.tzinfo is None:
        now = now.replace(tzinfo=None)
    return now >= cooldown_ends_at


def send_verification_email(email: str, code: str) -> None:
    if not settings.resend_api_key:
        raise EmailDeliveryError("RESEND_API_KEY is not configured")

    payload = {
        "from": settings.email_from,
        "to": [email],
        "subject": "Your ProjectForge verification code",
        "html": (
            "<p>Use this verification code to finish creating your ProjectForge account:</p>"
            f"<p style=\"font-size:28px;font-weight:700;letter-spacing:4px\">{code}</p>"
            f"<p>This code expires in {settings.email_verification_code_ttl_minutes} minutes.</p>"
        ),
        "text": (
            "Use this verification code to finish creating your ProjectForge account: "
            f"{code}\n\nThis code expires in "
            f"{settings.email_verification_code_ttl_minutes} minutes."
        ),
    }
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
        "Idempotency-Key": f"verify-{sha256(f'{email}:{code}'.encode('utf-8')).hexdigest()}",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post("https://api.resend.com/emails", json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise EmailDeliveryError("Failed to send verification email") from exc


def send_password_reset_email(email: str, code: str) -> None:
    if not settings.resend_api_key:
        raise EmailDeliveryError("RESEND_API_KEY is not configured")

    payload = {
        "from": settings.email_from,
        "to": [email],
        "subject": "Your ProjectForge password reset code",
        "html": (
            "<p>Use this verification code to reset your ProjectForge password:</p>"
            f"<p style=\"font-size:28px;font-weight:700;letter-spacing:4px\">{code}</p>"
            f"<p>This code expires in {settings.email_verification_code_ttl_minutes} minutes.</p>"
            "<p>If you did not request this, you can ignore this email.</p>"
        ),
        "text": (
            "Use this verification code to reset your ProjectForge password: "
            f"{code}\n\nThis code expires in "
            f"{settings.email_verification_code_ttl_minutes} minutes.\n\n"
            "If you did not request this, you can ignore this email."
        ),
    }
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
        "Idempotency-Key": f"reset-{sha256(f'{email}:{code}'.encode('utf-8')).hexdigest()}",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post("https://api.resend.com/emails", json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise EmailDeliveryError("Failed to send password reset email") from exc


def verification_error(detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)
