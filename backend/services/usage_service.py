from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.models.entities import UsageRecord, User, utcnow

GUEST_LIMIT_MESSAGE = "Login required to continue"


def _get_guest_record(db: Session, ip_address: str) -> UsageRecord | None:
    return db.scalar(
        select(UsageRecord)
        .where(UsageRecord.user_id.is_(None), UsageRecord.ip_address == ip_address)
        .order_by(desc(UsageRecord.last_request_time))
    )


def _get_user_record(db: Session, user_id: int) -> UsageRecord | None:
    return db.scalar(select(UsageRecord).where(UsageRecord.user_id == user_id))


def get_guest_requests_used(db: Session, ip_address: str) -> int:
    record = _get_guest_record(db, ip_address)
    return record.request_count if record else 0


def get_remaining_guest_requests(request_count: int, guest_limit: int) -> int:
    return max(guest_limit - request_count, 0)


def record_usage(db: Session, user: User | None, ip_address: str) -> UsageRecord:
    if user is None:
        record = _get_guest_record(db, ip_address)
        if record is None:
            record = UsageRecord(user_id=None, ip_address=ip_address, request_count=0)
    else:
        record = _get_user_record(db, user.id)
        if record is None:
            record = UsageRecord(user_id=user.id, ip_address=ip_address, request_count=0)
        record.ip_address = ip_address

    record.request_count += 1
    record.last_request_time = utcnow()
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

