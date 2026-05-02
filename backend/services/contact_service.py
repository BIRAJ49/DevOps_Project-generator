from html import escape

import httpx

from backend.utils.config import get_settings
from backend.utils.schemas import ContactRequest

settings = get_settings()


class ContactDeliveryError(RuntimeError):
    pass


def send_contact_message(payload: ContactRequest) -> None:
    if not settings.resend_api_key:
        raise ContactDeliveryError("RESEND_API_KEY is not configured")

    safe_name = escape(payload.name)
    safe_email = escape(str(payload.email))
    safe_subject = escape(payload.subject)
    safe_message = escape(payload.message).replace("\n", "<br>")

    email_payload = {
        "from": settings.email_from,
        "to": [settings.contact_recipient_email],
        "reply_to": str(payload.email),
        "subject": f"ProjectOps contact: {payload.subject}",
        "html": (
            "<h2>New ProjectOps contact message</h2>"
            f"<p><strong>Name:</strong> {safe_name}</p>"
            f"<p><strong>Email:</strong> {safe_email}</p>"
            f"<p><strong>Subject:</strong> {safe_subject}</p>"
            f"<p><strong>Message:</strong><br>{safe_message}</p>"
        ),
        "text": (
            "New ProjectOps contact message\n\n"
            f"Name: {payload.name}\n"
            f"Email: {payload.email}\n"
            f"Subject: {payload.subject}\n\n"
            f"{payload.message}"
        ),
    }
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                "https://api.resend.com/emails",
                json=email_payload,
                headers=headers,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ContactDeliveryError("Failed to send contact message") from exc
