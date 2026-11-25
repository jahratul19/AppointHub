import os
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Response,
    status,
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import get_db
from .models import (
    User,
    Appointment,
    AdminModerationLog,
    AuthSession,
    Group,
    GroupMember,
    GroupResource,
)
from .schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
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
    GroupCreate,
    GroupMemberCreate,
    GroupPermissionUpdate,
    GroupResourceCreate,
    GroupResourceUpdate,
)
from .security import decode_access_token
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
from datetime import datetime, timezone

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

COOKIE_SAMESITE = "none" if COOKIE_SECURE else "lax"


router = APIRouter(prefix="/api", tags=["AppointHUB"])

bearer_scheme = HTTPBearer()


# JWT VERIFICATION

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None or user.is_banned:
        raise credentials_exception

    return user

def get_current_admin(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

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

    return {
        "total_users": total_users,
        "banned_users": banned_users,
        "total_appointments": total_appointments,
        "pending_appointments": pending_appointments,
    }
    # ADMIN AUDIT LOGS
@router.get("/admin/audit-logs")
def get_admin_audit_logs(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    logs = (
        db.query(AdminModerationLog)
        .order_by(AdminModerationLog.created_at.desc())
        .limit(100)
        .all()
    )

    result = []

    for log in logs:
        admin = db.query(User).filter(
            User.id == log.admin_user_id
        ).first()

        target = db.query(User).filter(
            User.id == log.target_user_id
        ).first()

        result.append({
            "id": log.id,
            "admin_username": admin.username if admin else "Unknown",
            "target_username": target.username if target else "Unknown",
            "action": log.action,
            "reason": log.reason,
            "created_at": (
                log.created_at.isoformat()
                if log.created_at else None
            ),
        })

    return result


@router.get("/admin/users")
def get_admin_users(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid page or limit",
        )

    total_users = db.query(User).count()

    users = (
        db.query(User)
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

@router.put("/admin/users/{user_id}/ban")
def ban_admin_user(
    user_id: int,
    action_data: AdminUserAction,
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

    db.commit()

    return {"message": "User banned successfully"}


@router.put("/admin/users/{user_id}/unban")
def unban_admin_user(
    user_id: int,
    action_data: AdminUserAction,
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

    db.commit()

    return {"message": "User unbanned successfully"}

@router.put("/admin/users/{user_id}/role")
def update_admin_user_role(
    user_id: int,
    role_data: AdminRoleUpdate,
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

    db.commit()

    return {"message": "User role updated successfully"}

# ADMIN BULK USER ACTIONS
@router.post("/admin/users/bulk-action")
def bulk_admin_user_action(
    action_data: AdminBulkUserAction,
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

    db.commit()

    return {
        "message": "User sessions revoked successfully",
        "revoked_sessions": len(active_sessions),
    }

    # CREATE APPOINTMENT
@router.post(
    "/appointments/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_appointment_service(
        appointment_data,
        db,
        current_user,
    )
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delete_appointment_service(
        appointment_id, db, current_user
    )


# USER REGISTRATION
@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    return register_user_service(user_data, db)


# USER LOGIN
@router.post(
    "/auth/login",
    response_model=TokenResponse,
    tags=["Authentication"],
)
def login_user(
    user_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    result = login_user_service(user_data, db)

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


# CHANGE PASSWORD
@router.put(
    "/auth/change-password",
    tags=["Authentication"],
)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return change_password_service(
        current_user,
        password_data,
        db,
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

    result = refresh_user_session(refresh_token, db)

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
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token:
        logout_user_session(refresh_token, db)

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
    if not getattr(member, permission):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission for this action",
        )


# CREATE GROUP

@router.post("/groups")
def create_group(
    data: GroupCreate,
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
    check_group_permission(member, "can_manage_members")

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
    check_group_permission(member, "can_manage_members")

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
    check_group_permission(member, "can_manage_members")

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
    target.can_delete = data.can_delete
    target.can_manage_members = data.can_manage_members

    db.commit()

    return {"message": "Permissions updated successfully"}


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group, member = get_group_member(group_id, current_user, db)
    check_group_permission(member, "can_delete")

    resource = db.query(GroupResource).filter(
        GroupResource.id == resource_id,
        GroupResource.group_id == group_id,
    ).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    db.delete(resource)
    db.commit()

    return {"message": "Resource deleted successfully"}