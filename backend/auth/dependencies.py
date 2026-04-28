from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.auth.security import decode_access_token
from backend.models.database import get_db
from backend.models.entities import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None

    payload = decode_access_token(token)
    subject = payload.get("sub")
    if subject is None:
        raise _credentials_exception()

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise _credentials_exception() from exc

    user = db.get(User, user_id)
    if user is None:
        raise _credentials_exception()

    return user


def get_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    if user is None:
        raise _credentials_exception()
    return user

