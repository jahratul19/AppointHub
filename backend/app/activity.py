from datetime import datetime, timedelta, timezone

from fastapi import Request
from sqlalchemy.orm import Session

from .models import UserActivity


def request_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()[:64]
    return request.client.host[:64] if request.client else None


def record_activity(
    db: Session,
    event_type: str,
    request: Request,
    actor_user_id: int | None = None,
    target_user_id: int | None = None,
    account_identifier: str | None = None,
    details: str = "",
) -> UserActivity:
    activity = UserActivity(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        event_type=event_type,
        account_identifier=(account_identifier or "")[:254] or None,
        ip_address=request_ip(request),
        user_agent=request.headers.get("user-agent", "")[:500],
        details=details[:2000],
        created_at=datetime.now(timezone.utc),
    )
    db.add(activity)
    return activity


def recent_failed_logins(
    db: Session,
    account_identifier: str,
    ip_address: str | None,
    minutes: int = 15,
) -> int:
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    query = db.query(UserActivity.id).filter(
        UserActivity.event_type == "failed_login",
        UserActivity.created_at >= since,
    )
    if account_identifier and ip_address:
        from sqlalchemy import or_

        query = query.filter(
            or_(
                UserActivity.account_identifier == account_identifier,
                UserActivity.ip_address == ip_address,
            )
        )
    elif account_identifier:
        query = query.filter(
            UserActivity.account_identifier == account_identifier
        )
    elif ip_address:
        query = query.filter(UserActivity.ip_address == ip_address)
    else:
        return 0
    return query.count()
