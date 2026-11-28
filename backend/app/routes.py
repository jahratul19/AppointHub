import os
import csv
import io
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from .database import get_db
from .models import (
    User,
    Appointment,
    Doctor,
    AdminModerationLog,
    AuthSession,
    Group,
    GroupMember,
    GroupResource,
    UserActivity,
)
from .schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    DoctorCreate,
    DoctorUpdate,
    DoctorResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    AuthSessionResponse,
    UserUpdate,
    PasswordChange,
    AdminUserAction,
    AdminRoleUpdate,
    AdminBulkUserAction,
    AdminBulkDelete,
    GroupCreate,
    GroupUpdate,
    GroupMemberCreate,
    GroupPermissionUpdate,
    GroupResourceCreate,
    GroupResourceUpdate,
)
from .security import decode_access_token
from .activity import record_activity
from .rbac import (
    GROUP_CREATE,
    GROUP_DELETE,
    GROUP_EDIT,
    GROUP_VIEW,
    ROLE_ADMIN,
    require_group_permission,
    require_role,
)
from .services import (
    create_appointment_service,
    get_appointments_service,
    get_appointment_service,
    update_appointment_service,
    delete_appointment_service,
    register_user_service,
    login_user_service,
    refresh_user_session,
    logout_user_session,
    get_user_sessions,
    revoke_user_session,
    update_user_profile_service,
    change_password_service,
)
from datetime import datetime, timedelta, timezone

COOKIE_SECURE = os.getenv(
    "COOKIE_SECURE",
    "true" if os.getenv("VERCEL") == "1" else "false",
).lower() == "true"

COOKIE_SAMESITE = "none" if COOKIE_SECURE else "lax"


router = APIRouter(prefix="/api", tags=["AppointHUB"])

bearer_scheme = HTTPBearer(auto_error=False)


# JWT VERIFICATION

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        session_id = payload.get("sid")

        if user_id is None or session_id is None:
            raise credentials_exception

        user_id = int(user_id)
        session_id = int(session_id)

    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    auth_session = db.query(AuthSession).filter(
        AuthSession.id == session_id,
        AuthSession.user_id == user_id,
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > datetime.now(timezone.utc),
    ).first()

    if user is None or user.is_banned or auth_session is None:
        raise credentials_exception

    return user

def get_current_admin(
    current_user: User = Depends(get_current_user),
):
    require_role(current_user.role, ROLE_ADMIN)
    return current_user


@router.get("/admin/dashboard/stats")
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    total_users = db.query(User).count()

    banned_users = db.query(User).filter(
        User.is_banned.is_(True)
    ).count()

    total_appointments = db.query(Appointment).count()

    pending_appointments = db.query(Appointment).filter(
        Appointment.status == "Pending"
    ).count()
    total_groups = db.query(Group).count()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    def recent_count(event_type: str) -> int:
        return db.query(UserActivity).filter(
            UserActivity.event_type == event_type,
            UserActivity.created_at >= week_ago,
        ).count()

    return {
        "total_users": total_users,
        "banned_users": banned_users,
        "total_appointments": total_appointments,
        "pending_appointments": pending_appointments,
        "total_records": total_appointments,
        "total_groups": total_groups,
        "new_users_7d": recent_count("signup"),
        "new_records_7d": recent_count("record_created"),
        "new_groups_7d": recent_count("group_created"),
    }


@router.get("/admin/audit-logs")
def get_admin_audit_logs(
    page: int = 1,
    limit: int = 50,
    event_type: str | None = None,
    search: str | None = None,
    ip_address: str | None = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Invalid page or limit")
    query = db.query(UserActivity)
    if event_type:
        query = query.filter(UserActivity.event_type == event_type)
    if ip_address:
        query = query.filter(UserActivity.ip_address == ip_address)
    if search:
        term = f"%{search.strip()}%"
        matching_user_ids = db.query(User.id).filter(
            User.username.ilike(term)
        )
        query = query.filter(or_(
            UserActivity.event_type.ilike(term),
            UserActivity.account_identifier.ilike(term),
            UserActivity.details.ilike(term),
            UserActivity.ip_address.ilike(term),
            UserActivity.actor_user_id.in_(matching_user_ids),
            UserActivity.target_user_id.in_(matching_user_ids),
        ))
    total = query.count()
    logs = query.order_by(UserActivity.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    user_ids = {
        user_id
        for log in logs
        for user_id in (log.actor_user_id, log.target_user_id)
        if user_id is not None
    }
    users = {
        user.id: user.username
        for user in db.query(User).filter(User.id.in_(user_ids)).all()
    } if user_ids else {}
    return {
        "events": [{
            "id": log.id,
            "actor_user_id": log.actor_user_id,
            "admin_username": users.get(log.actor_user_id, "Unknown"),
            "target_user_id": log.target_user_id,
            "target_username": users.get(log.target_user_id, log.account_identifier or "Unknown"),
            "action": log.event_type,
            "event_type": log.event_type,
            "reason": log.details,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        } for log in logs],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


@router.get("/admin/users")
def get_admin_users(
    page: int = 1,
    limit: int = 10,
    search: str | None = None,
    role: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid page or limit",
        )

    query = db.query(User)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(
            User.username.ilike(term),
            User.email.ilike(term),
        ))
    if role in {"admin", "user"}:
        query = query.filter(User.role == role)
    elif role:
        raise HTTPException(status_code=400, detail="Invalid role filter")
    if status_filter == "active":
        query = query.filter(User.is_banned.is_(False))
    elif status_filter == "banned":
        query = query.filter(User.is_banned.is_(True))
    elif status_filter:
        raise HTTPException(status_code=400, detail="Invalid status filter")

    total_users = query.count()
    users = (
        query
        .order_by(User.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_banned": user.is_banned,
            }
            for user in users
        ],
        "total": total_users,
        "page": page,
        "limit": limit,
        "total_pages": (total_users + limit - 1) // limit,
    }


@router.get("/admin/users/{user_id}")
def get_admin_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    appointments = db.query(Appointment).filter(
        Appointment.user_id == user_id
    ).order_by(Appointment.id.desc()).all()
    memberships = db.query(GroupMember).filter(
        GroupMember.user_id == user_id
    ).all()
    groups = []
    for membership in memberships:
        group = db.query(Group).filter(Group.id == membership.group_id).first()
        if group:
            groups.append({
                "id": group.id,
                "name": group.name,
                "owner_id": group.owner_id,
            })
    sessions = db.query(AuthSession).filter(
        AuthSession.user_id == user_id
    ).order_by(AuthSession.created_at.desc()).all()
    activity = db.query(UserActivity).filter(
        or_(
            UserActivity.actor_user_id == user_id,
            UserActivity.target_user_id == user_id,
        )
    ).order_by(UserActivity.created_at.desc()).limit(20).all()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_banned": user.is_banned,
        "appointments": [{
            "id": item.id,
            "customer_name": item.customer_name,
            "provider_name": item.provider_name,
            "doctor_id": item.doctor_id,
            "appointment_date": item.appointment_date.isoformat(),
            "appointment_time": item.appointment_time.isoformat(),
            "status": item.status,
            "reason": item.reason,
        } for item in appointments],
        "groups": groups,
        "sessions": [{
            "id": item.id,
            "created_at": item.created_at.isoformat(),
            "expires_at": item.expires_at.isoformat(),
            "revoked_at": item.revoked_at.isoformat() if item.revoked_at else None,
        } for item in sessions],
        "recent_activity": [{
            "event_type": item.event_type,
            "ip_address": item.ip_address,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "details": item.details,
        } for item in activity],
    }


@router.get("/admin/security/failed-logins")
def get_failed_login_summary(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Invalid limit")
    since = datetime.now(timezone.utc) - timedelta(days=7)
    failures = db.query(UserActivity).filter(
        UserActivity.event_type == "failed_login",
        UserActivity.created_at >= since,
    )
    by_ip = db.query(
        UserActivity.ip_address,
        func.count(UserActivity.id).label("attempts"),
    ).filter(
        UserActivity.event_type == "failed_login",
        UserActivity.created_at >= since,
        UserActivity.ip_address.is_not(None),
    ).group_by(UserActivity.ip_address).order_by(
        func.count(UserActivity.id).desc()
    ).limit(limit).all()
    by_account = db.query(
        UserActivity.account_identifier,
        func.count(UserActivity.id).label("attempts"),
    ).filter(
        UserActivity.event_type == "failed_login",
        UserActivity.created_at >= since,
        UserActivity.account_identifier.is_not(None),
    ).group_by(UserActivity.account_identifier).order_by(
        func.count(UserActivity.id).desc()
    ).limit(limit).all()
    return {
        "failed_login_count_7d": failures.count(),
        "by_ip": [{"ip_address": ip, "attempts": count} for ip, count in by_ip],
        "by_account": [
            {"account": account, "attempts": count}
            for account, count in by_account
        ],
    }


@router.get("/admin/content/appointments")
def get_all_admin_appointments(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    appointment_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Invalid page or limit")
    query = db.query(Appointment)
    if appointment_status:
        query = query.filter(Appointment.status == appointment_status)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(
            Appointment.customer_name.ilike(term),
            Appointment.provider_name.ilike(term),
            Appointment.reason.ilike(term),
        ))
    total = query.count()
    items = query.order_by(Appointment.id.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    return {
        "records": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }


@router.get("/admin/content/groups")
def get_all_admin_groups(
    search: str | None = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    query = db.query(Group)
    if search:
        query = query.filter(Group.name.ilike(f"%{search.strip()}%"))
    return query.order_by(Group.id.desc()).all()


@router.delete("/admin/content/appointments/{appointment_id}")
def admin_delete_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    if appointment is None:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(appointment)
    record_activity(
        db, "delete_record", request, actor_user_id=current_admin.id,
        target_user_id=appointment.user_id, details=f"Appointment {appointment_id}",
    )
    db.commit()
    return {"message": "Record deleted"}


@router.post("/admin/content/appointments/bulk-delete")
def admin_bulk_delete_appointments(
    data: AdminBulkDelete,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    records = db.query(Appointment).filter(
        Appointment.id.in_(data.record_ids)
    ).all()
    if len(records) != len(set(data.record_ids)):
        raise HTTPException(status_code=404, detail="One or more records not found")
    for record in records:
        record_activity(
            db, "delete_record", request, actor_user_id=current_admin.id,
            target_user_id=record.user_id, details=f"Appointment {record.id}",
        )
        db.delete(record)
    db.commit()
    return {"deleted_count": len(records)}


@router.delete("/admin/content/groups/{group_id}")
def admin_delete_group(
    group_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    db.query(GroupResource).filter(GroupResource.group_id == group_id).delete()
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    db.delete(group)
    record_activity(
        db, "delete_group", request, actor_user_id=current_admin.id,
        target_user_id=group.owner_id,
        details=f"Group {group.name} (ID {group_id})",
    )
    db.commit()
    return {"message": "Group deleted"}


@router.post("/admin/content/groups/bulk-delete")
def admin_bulk_delete_groups(
    data: AdminBulkDelete,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    groups = db.query(Group).filter(Group.id.in_(data.record_ids)).all()
    if len(groups) != len(set(data.record_ids)):
        raise HTTPException(status_code=404, detail="One or more groups not found")
    for group in groups:
        db.query(GroupResource).filter(
            GroupResource.group_id == group.id
        ).delete()
        db.query(GroupMember).filter(
            GroupMember.group_id == group.id
        ).delete()
        record_activity(
            db, "delete_group", request, actor_user_id=current_admin.id,
            target_user_id=group.owner_id,
            details=f"Group {group.name} (ID {group.id})",
        )
        db.delete(group)
    db.commit()
    return {"deleted_count": len(groups)}


def _csv_value(value):
    text = "" if value is None else str(value)
    if text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _csv_response(filename: str, headers: list[str], rows: list[list[object]]):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_csv_value(value) for value in row])
    return Response(
        content="\ufeff" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/admin/export/users.csv")
def export_admin_users(
    request: Request,
    search: str | None = None,
    role: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if role and role not in {"admin", "user"}:
        raise HTTPException(status_code=400, detail="Invalid role filter")
    if status_filter and status_filter not in {"active", "banned"}:
        raise HTTPException(status_code=400, detail="Invalid status filter")
    query = db.query(User)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(User.username.ilike(term), User.email.ilike(term)))
    if role in {"admin", "user"}:
        query = query.filter(User.role == role)
    if status_filter == "active":
        query = query.filter(User.is_banned.is_(False))
    elif status_filter == "banned":
        query = query.filter(User.is_banned.is_(True))
    users = query.order_by(User.id).all()
    record_activity(db, "export_users", request, actor_user_id=current_admin.id)
    db.commit()
    return _csv_response(
        "users.csv",
        ["id", "username", "email", "role", "status"],
        [[u.id, u.username, u.email, u.role, "banned" if u.is_banned else "active"] for u in users],
    )


@router.get("/admin/export/records.csv")
def export_admin_records(
    request: Request,
    search: str | None = None,
    appointment_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    query = db.query(Appointment)
    if appointment_status:
        query = query.filter(Appointment.status == appointment_status)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(
            Appointment.customer_name.ilike(term),
            Appointment.provider_name.ilike(term),
            Appointment.reason.ilike(term),
        ))
    records = query.order_by(Appointment.id).all()
    record_activity(db, "export_records", request, actor_user_id=current_admin.id)
    db.commit()
    return _csv_response(
        "records.csv",
        ["id", "owner_user_id", "customer_name", "provider_name", "doctor_id",
         "date", "time", "reason", "status"],
        [[r.id, r.user_id, r.customer_name, r.provider_name, r.doctor_id,
          r.appointment_date, r.appointment_time, r.reason, r.status]
         for r in records],
    )


@router.get("/admin/export/activity.csv")
def export_admin_activity(
    request: Request,
    event_type: str | None = None,
    search: str | None = None,
    ip_address: str | None = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if event_type and len(event_type) > 50:
        raise HTTPException(status_code=400, detail="Invalid event type filter")
    query = db.query(UserActivity)
    if event_type:
        query = query.filter(UserActivity.event_type == event_type)
    if ip_address:
        query = query.filter(UserActivity.ip_address == ip_address)
    if search:
        term = f"%{search.strip()}%"
        matching_user_ids = db.query(User.id).filter(
            User.username.ilike(term)
        )
        query = query.filter(or_(
            UserActivity.event_type.ilike(term),
            UserActivity.account_identifier.ilike(term),
            UserActivity.details.ilike(term),
            UserActivity.ip_address.ilike(term),
            UserActivity.actor_user_id.in_(matching_user_ids),
            UserActivity.target_user_id.in_(matching_user_ids),
        ))
    events = query.order_by(UserActivity.created_at).all()
    record_activity(db, "export_activity", request, actor_user_id=current_admin.id)
    db.commit()
    return _csv_response(
        "activity.csv",
        ["id", "event_type", "actor_user_id", "target_user_id", "account",
         "ip_address", "user_agent", "details", "created_at"],
        [[e.id, e.event_type, e.actor_user_id, e.target_user_id,
          e.account_identifier, e.ip_address, e.user_agent, e.details, e.created_at]
         for e in events],
    )


@router.put("/admin/users/{user_id}/ban")
def ban_admin_user(
    user_id: int,
    action_data: AdminUserAction,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if not action_data.reason.strip():
        raise HTTPException(
            status_code=400,
            detail="Ban reason is required",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.id == current_admin.id or user.role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Cannot ban this user",
        )

    user.is_banned = True

    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    ).update(
        {"revoked_at": datetime.now(timezone.utc)},
        synchronize_session=False,
    )

    db.add(
        AdminModerationLog(
            admin_user_id=current_admin.id,
            target_user_id=user.id,
            action="ban",
            reason=action_data.reason.strip(),
        )
    )
    record_activity(
        db, "ban", request, actor_user_id=current_admin.id,
        target_user_id=user.id, details=action_data.reason.strip(),
    )

    db.commit()

    return {"message": "User banned successfully"}


@router.put("/admin/users/{user_id}/unban")
def unban_admin_user(
    user_id: int,
    action_data: AdminUserAction,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if not action_data.reason.strip():
        raise HTTPException(
            status_code=400,
            detail="Unban reason is required",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    user.is_banned = False

    db.add(
        AdminModerationLog(
            admin_user_id=current_admin.id,
            target_user_id=user.id,
            action="unban",
            reason=action_data.reason.strip(),
        )
    )
    record_activity(
        db, "unban", request, actor_user_id=current_admin.id,
        target_user_id=user.id, details=action_data.reason.strip(),
    )

    db.commit()

    return {"message": "User unbanned successfully"}

@router.put("/admin/users/{user_id}/role")
def update_admin_user_role(
    user_id: int,
    role_data: AdminRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if role_data.role not in ["admin", "user"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own role",
        )

    user.role = role_data.role

    db.add(
        AdminModerationLog(
            admin_user_id=current_admin.id,
            target_user_id=user.id,
            action="role_change",
            reason=f"Role changed to {role_data.role}",
        )
    )
    record_activity(
        db, "role_change", request, actor_user_id=current_admin.id,
        target_user_id=user.id, details=f"Role changed to {role_data.role}",
    )
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    ).update(
        {"revoked_at": datetime.now(timezone.utc)},
        synchronize_session=False,
    )

    db.commit()

    return {"message": "User role updated successfully"}

# ADMIN BULK USER ACTIONS
@router.post("/admin/users/bulk-action")
def bulk_admin_user_action(
    action_data: AdminBulkUserAction,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if action_data.action not in ["ban", "unban"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid action",
        )

    if not action_data.reason.strip():
        raise HTTPException(
            status_code=400,
            detail="Reason is required",
        )

    if not action_data.user_ids:
        raise HTTPException(
            status_code=400,
            detail="No users selected",
        )

    users = (
        db.query(User)
        .filter(User.id.in_(action_data.user_ids))
        .all()
    )

    if len(users) != len(set(action_data.user_ids)):
        raise HTTPException(
            status_code=404,
            detail="One or more users not found",
        )

    processed_count = 0

    for user in users:
        if user.id == current_admin.id:
            continue

        if action_data.action == "ban":
            if user.role == "admin":
                continue

            user.is_banned = True

            db.query(AuthSession).filter(
    AuthSession.user_id == user.id,
    AuthSession.revoked_at.is_(None),
).update(
    {"revoked_at": datetime.now(timezone.utc)},
    synchronize_session=False,
)

        else:
            user.is_banned = False

        db.add(
            AdminModerationLog(
                admin_user_id=current_admin.id,
                target_user_id=user.id,
                action=action_data.action,
                reason=action_data.reason.strip(),
            )
        )
        record_activity(
            db, action_data.action, request, actor_user_id=current_admin.id,
            target_user_id=user.id, details=action_data.reason.strip(),
        )

        processed_count += 1

    db.commit()

    return {
        "message": "Bulk action completed",
        "processed_count": processed_count,
    }
    # ADMIN REVOKE USER SESSIONS
@router.delete("/admin/users/{user_id}/sessions")
def revoke_admin_user_sessions(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    active_sessions = db.query(AuthSession).filter(
        AuthSession.user_id == user_id,
        AuthSession.revoked_at.is_(None),
    ).all()

    now = datetime.now(timezone.utc)

    for session in active_sessions:
        session.revoked_at = now

    db.add(
        AdminModerationLog(
            admin_user_id=current_admin.id,
            target_user_id=user.id,
            action="session_revoke",
            reason="Admin revoked all active sessions",
        )
    )
    record_activity(
        db, "session_revoke", request, actor_user_id=current_admin.id,
        target_user_id=user.id,
        details=f"Revoked {len(active_sessions)} sessions",
    )

    db.commit()

    return {
        "message": "User sessions revoked successfully",
        "revoked_sessions": len(active_sessions),
    }

@router.get("/doctors", response_model=list[DoctorResponse])
def list_available_doctors(
    db: Session = Depends(get_db),
):
    return db.query(Doctor).filter(
        Doctor.is_active.is_(True)
    ).order_by(Doctor.name).all()


@router.get("/admin/doctors", response_model=list[DoctorResponse])
def list_admin_doctors(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return db.query(Doctor).order_by(Doctor.name).all()


@router.post(
    "/admin/doctors",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_doctor(
    doctor_data: DoctorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    doctor = Doctor(
        name=doctor_data.name,
        photo_url=doctor_data.photo_url,
        specialty=doctor_data.specialty,
        description=doctor_data.description.strip(),
        is_active=doctor_data.is_active,
    )
    db.add(doctor)
    db.flush()
    record_activity(
        db, "doctor_created", request, actor_user_id=current_admin.id,
        details=f"Doctor {doctor.name} (ID {doctor.id})",
    )
    db.commit()
    db.refresh(doctor)
    return doctor


@router.put(
    "/admin/doctors/{doctor_id}",
    response_model=DoctorResponse,
)
def update_doctor(
    doctor_id: int,
    doctor_data: DoctorUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    for field, value in doctor_data.model_dump().items():
        setattr(doctor, field, value.strip() if field == "description" else value)
    record_activity(
        db, "doctor_updated", request, actor_user_id=current_admin.id,
        details=f"Doctor {doctor.name} (ID {doctor.id})",
    )
    db.commit()
    db.refresh(doctor)
    return doctor


@router.post(
    "/admin/doctors/{doctor_id}/deactivate",
    response_model=DoctorResponse,
)
def deactivate_doctor(
    doctor_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.is_active = False
    record_activity(
        db, "doctor_deactivated", request, actor_user_id=current_admin.id,
        details=f"Doctor {doctor.name} (ID {doctor.id})",
    )
    db.commit()
    db.refresh(doctor)
    return doctor


# CREATE APPOINTMENT
@router.post(
    "/appointments/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(
    appointment_data: AppointmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = create_appointment_service(
        appointment_data,
        db,
        current_user,
    )
    record_activity(
        db, "record_created", request, actor_user_id=current_user.id,
        target_user_id=current_user.id, details=f"Appointment {appointment.id}",
    )
    db.commit()
    return appointment
# READ ALL APPOINTMENTS
@router.get(
    "/appointments/",
    response_model=list[AppointmentResponse],
)
def get_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_appointments_service(db, current_user)


# READ SINGLE APPOINTMENT
@router.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_appointment_service(
        appointment_id, db, current_user
    )


# UPDATE APPOINTMENT
@router.put(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
)
def update_appointment(
    appointment_id: int,
    updated_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_appointment_service(
        appointment_id, updated_data, db, current_user
    )


# DELETE APPOINTMENT
@router.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = get_appointment_service(
        appointment_id, db, current_user
    )
    result = delete_appointment_service(
        appointment_id, db, current_user
    )
    record_activity(
        db, "delete_record", request, actor_user_id=current_user.id,
        target_user_id=appointment.user_id, details=f"Appointment {appointment_id}",
    )
    db.commit()
    return result


# USER REGISTRATION
@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    user = register_user_service(user_data, db)
    record_activity(
        db, "signup", request, actor_user_id=user.id,
        target_user_id=user.id, account_identifier=user.email.lower(),
    )
    db.commit()
    return user


# USER LOGIN
@router.post(
    "/auth/login",
    response_model=TokenResponse,
    tags=["Authentication"],
)
def login_user(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    result = login_user_service(user_data, db, request)

    refresh_token = result.pop("refresh_token")

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=7 * 24 * 60 * 60,
        path="/api/auth",
    )

    return result


# UPDATE PROFILE
@router.put(
    "/auth/profile",
    response_model=UserResponse,
    tags=["Authentication"],
)
def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_user_profile_service(
        current_user,
        user_data,
        db,
    )


@router.get(
    "/auth/me",
    response_model=UserResponse,
    tags=["Authentication"],
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


# CHANGE PASSWORD
@router.put(
    "/auth/change-password",
    tags=["Authentication"],
)
def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return change_password_service(
        current_user,
        password_data,
        db,
        request,
    )

    # REFRESH ACCESS TOKEN
@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    tags=["Authentication"],
)
def refresh_access_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        result = refresh_user_session(refresh_token, db)
    except HTTPException as error:
        failure = JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail},
            headers=error.headers,
        )
        failure.delete_cookie(
            key="refresh_token",
            path="/api/auth",
            secure=COOKIE_SECURE,
            httponly=True,
            samesite=COOKIE_SAMESITE,
        )
        return failure

    new_refresh_token = result.pop("refresh_token")

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=7 * 24 * 60 * 60,
        path="/api/auth",
    )

    return result
# USER LOGOUT
@router.post(
    "/auth/logout",
    tags=["Authentication"],
)
def logout_user(
    response: Response,
    request: Request,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    user_id = None
    if refresh_token:
        user_id = logout_user_session(refresh_token, db)
    record_activity(
        db, "logout", request, actor_user_id=user_id, target_user_id=user_id,
    )
    db.commit()

    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite=COOKIE_SAMESITE,
    )

    return {"message": "Logged out successfully"}


# VIEW MY SESSIONS
@router.get(
    "/auth/sessions",
    response_model=list[AuthSessionResponse],
    tags=["Authentication"],
)
def view_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_sessions(current_user.id, db)


# REVOKE MY SESSION
@router.delete(
    "/auth/sessions/{session_id}",
    tags=["Authentication"],
)
def revoke_my_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return revoke_user_session(
        session_id,
        current_user.id,
        db,
    )
# GROUP PERMISSION HELPER

def get_group_member(
    group_id: int,
    current_user: User,
    db: Session,
):
    group = db.query(Group).filter(
        Group.id == group_id
    ).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Group access denied")

    return group, member


def check_group_permission(member: GroupMember, permission: str):
    require_group_permission(member, permission)


def require_group_owner(group: Group, current_user: User) -> None:
    if group.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the group owner can manage this group",
        )


# CREATE GROUP

@router.post("/groups")
def create_group(
    data: GroupCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Group name is required")

    group = Group(
        name=data.name.strip(),
        owner_id=current_user.id,
    )

    db.add(group)
    db.flush()

    owner_membership = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        can_view=True,
        can_create=True,
        can_edit=True,
        can_delete=True,
        can_manage_members=True,
    )

    db.add(owner_membership)
    record_activity(
        db, "group_created", request, actor_user_id=current_user.id,
        target_user_id=current_user.id, details=data.name.strip(),
    )
    db.commit()
    db.refresh(group)

    return {
        "id": group.id,
        "name": group.name,
        "owner_id": group.owner_id,
    }


# VIEW MY GROUPS

@router.get("/groups")
def get_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memberships = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id
    ).all()

    result = []

    for membership in memberships:
        group = db.query(Group).filter(
            Group.id == membership.group_id
        ).first()

        if group:
            result.append({
                "id": group.id,
                "name": group.name,
                "owner_id": group.owner_id,
                "permissions": {
                    "can_view": membership.can_view,
                    "can_create": membership.can_create,
                    "can_edit": membership.can_edit,
                    "can_delete": membership.can_delete,
                    "can_manage_members": group.owner_id == current_user.id,
                },
            })

    return result


# ADD GROUP MEMBER

@router.post("/groups/{group_id}/members")
def add_group_member(
    group_id: int,
    data: GroupMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, member = get_group_member(group_id, current_user, db)
    require_group_owner(group, current_user)

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user.id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    new_member = GroupMember(
        group_id=group_id,
        user_id=user.id,
        can_view=True,
        can_create=False,
        can_edit=False,
        can_delete=False,
        can_manage_members=False,
    )

    db.add(new_member)
    db.commit()

    return {"message": "Member added successfully"}


# VIEW GROUP MEMBERS

@router.get("/groups/{group_id}/members")
def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, member = get_group_member(group_id, current_user, db)
    require_group_owner(group, current_user)

    memberships = db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()

    result = []

    for item in memberships:
        user = db.query(User).filter(
            User.id == item.user_id
        ).first()

        if user:
            result.append({
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "can_view": item.can_view,
                "can_create": item.can_create,
                "can_edit": item.can_edit,
                "can_delete": item.can_delete,
                "can_manage_members": item.can_manage_members,
            })

    return result


# UPDATE MEMBER PERMISSIONS

@router.put("/groups/{group_id}/members/{user_id}/permissions")
def update_group_permissions(
    group_id: int,
    user_id: int,
    data: GroupPermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, member = get_group_member(group_id, current_user, db)
    require_group_owner(group, current_user)

    target = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).first()

    if not target:
        raise HTTPException(status_code=404, detail="Group member not found")

    if user_id == group.owner_id:
        raise HTTPException(status_code=400, detail="Owner permissions cannot be changed")

    target.can_view = data.can_view
    target.can_create = data.can_create
    target.can_edit = data.can_edit
    target.can_delete = False
    target.can_manage_members = False

    db.commit()

    return {"message": "Permissions updated successfully"}


@router.put("/groups/{group_id}")
def rename_group(
    group_id: int,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, _ = get_group_member(group_id, current_user, db)
    require_group_owner(group, current_user)
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Group name is required")
    group.name = name
    db.commit()
    return {"id": group.id, "name": group.name, "owner_id": group.owner_id}


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, _ = get_group_member(group_id, current_user, db)
    require_group_owner(group, current_user)
    db.query(GroupResource).filter(GroupResource.group_id == group_id).delete()
    db.query(GroupMember).filter(GroupMember.group_id == group_id).delete()
    db.delete(group)
    record_activity(
        db, "delete_group", request, actor_user_id=current_user.id,
        target_user_id=current_user.id, details=f"Group {group.name}",
    )
    db.commit()
    return {"message": "Group deleted"}


@router.delete("/groups/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, _ = get_group_member(group_id, current_user, db)
    require_group_owner(group, current_user)
    if user_id == group.owner_id:
        raise HTTPException(status_code=400, detail="The owner cannot be removed")
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Group member not found")
    db.delete(member)
    db.commit()
    return {"message": "Member removed"}


# VIEW GROUP RESOURCES

@router.get("/groups/{group_id}/resources")
def get_group_resources(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, member = get_group_member(group_id, current_user, db)
    check_group_permission(member, "can_view")

    resources = db.query(GroupResource).filter(
        GroupResource.group_id == group_id
    ).all()

    return resources


# CREATE GROUP RESOURCE

@router.post("/groups/{group_id}/resources")
def create_group_resource(
    group_id: int,
    data: GroupResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, member = get_group_member(group_id, current_user, db)
    check_group_permission(member, "can_create")

    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    resource = GroupResource(
        group_id=group_id,
        created_by=current_user.id,
        title=data.title.strip(),
        description=data.description,
    )

    db.add(resource)
    db.commit()
    db.refresh(resource)

    return resource


# UPDATE GROUP RESOURCE

@router.put("/groups/{group_id}/resources/{resource_id}")
def update_group_resource(
    group_id: int,
    resource_id: int,
    data: GroupResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, member = get_group_member(group_id, current_user, db)
    check_group_permission(member, "can_edit")

    resource = db.query(GroupResource).filter(
        GroupResource.id == resource_id,
        GroupResource.group_id == group_id,
    ).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if not data.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    resource.title = data.title.strip()
    resource.description = data.description

    db.commit()
    db.refresh(resource)

    return resource


# DELETE GROUP RESOURCE

@router.delete("/groups/{group_id}/resources/{resource_id}")
def delete_group_resource(
    group_id: int,
    resource_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, member = get_group_member(group_id, current_user, db)
    require_group_owner(group, current_user)

    resource = db.query(GroupResource).filter(
        GroupResource.id == resource_id,
        GroupResource.group_id == group_id,
    ).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    db.delete(resource)
    record_activity(
        db, "delete_record", request, actor_user_id=current_user.id,
        target_user_id=current_user.id,
        details=f"Group resource {resource_id} in group {group_id}",
    )
    db.commit()

    return {"message": "Resource deleted successfully"}