from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user_optional
from backend.models.database import get_db
from backend.models.entities import User
from backend.services.openrouter_service import OpenRouterServiceError, get_project_suggestions
from backend.services.usage_service import (
    GUEST_LIMIT_MESSAGE,
    get_guest_requests_used,
    get_remaining_guest_requests,
    record_usage,
)
from backend.utils.config import get_settings
from backend.utils.rate_limiter import rate_limit
from backend.utils.request import extract_client_ip
from backend.utils.schemas import SuggestRequest, SuggestResponse

router = APIRouter(tags=["suggestions"])
settings = get_settings()
suggest_rate_limit = rate_limit(
    "suggest",
    settings.rate_limit_max_requests,
    settings.rate_limit_window_seconds,
    settings.rate_limit_max_buckets,
)


@router.post("/suggest", response_model=SuggestResponse, dependencies=[Depends(suggest_rate_limit)])
def suggest_projects(
    payload: SuggestRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> SuggestResponse:
    client_ip = extract_client_ip(request)

    if user is None:
        guest_requests_used = get_guest_requests_used(db, client_ip)
        if guest_requests_used >= settings.guest_project_limit:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=GUEST_LIMIT_MESSAGE)

    try:
        suggestions = get_project_suggestions(payload.prompt)
    except OpenRouterServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    usage_record = record_usage(db, user=user, ip_address=client_ip)
    guest_requests_remaining = (
        None
        if user is not None
        else get_remaining_guest_requests(usage_record.request_count, settings.guest_project_limit)
    )

    return SuggestResponse(
        suggestions=suggestions,
        is_authenticated=user is not None,
        guest_requests_remaining=guest_requests_remaining,
    )
