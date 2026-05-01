from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user_optional
from backend.models.database import get_db
from backend.models.entities import User
from backend.services.openrouter_service import OpenRouterServiceError, get_project_details
from backend.services.usage_service import (
    GUEST_LIMIT_MESSAGE,
    get_guest_requests_used,
    get_remaining_guest_requests,
    record_usage,
)
from backend.utils.config import get_settings
from backend.utils.rate_limiter import rate_limit
from backend.utils.request import extract_client_ip
from backend.utils.schemas import ProjectDetailsRequest, ProjectDetailsResponse

router = APIRouter(tags=["details"])
settings = get_settings()
details_rate_limit = rate_limit(
    "details",
    settings.rate_limit_max_requests,
    settings.rate_limit_window_seconds,
    settings.rate_limit_max_buckets,
)


@router.post(
    "/details",
    response_model=ProjectDetailsResponse,
    dependencies=[Depends(details_rate_limit)],
)
def project_details(
    payload: ProjectDetailsRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
) -> ProjectDetailsResponse:
    client_ip = extract_client_ip(request)

    if user is None:
        guest_requests_used = get_guest_requests_used(db, client_ip)
        if guest_requests_used >= settings.guest_project_limit:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=GUEST_LIMIT_MESSAGE)

    try:
        details = get_project_details(
            user_prompt=payload.prompt,
            suggestion=payload.suggestion.model_dump(mode="json"),
        )
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

    response = ProjectDetailsResponse.model_validate(details)
    response.is_authenticated = user is not None
    response.guest_requests_remaining = guest_requests_remaining
    return response
