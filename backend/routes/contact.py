from fastapi import APIRouter, Depends, HTTPException, status

from backend.services.contact_service import ContactDeliveryError, send_contact_message
from backend.utils.config import get_settings
from backend.utils.rate_limiter import rate_limit
from backend.utils.schemas import ContactRequest, ContactResponse

router = APIRouter(tags=["contact"])
settings = get_settings()
contact_rate_limit = rate_limit(
    "contact",
    settings.rate_limit_max_requests,
    settings.rate_limit_window_seconds,
    settings.rate_limit_max_buckets,
)


@router.post(
    "/contact",
    response_model=ContactResponse,
    dependencies=[Depends(contact_rate_limit)],
)
def contact(payload: ContactRequest) -> ContactResponse:
    try:
        send_contact_message(payload)
    except ContactDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return ContactResponse(message="Message sent successfully.")
