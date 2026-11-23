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
from .models import User, Appointment, AdminModerationLog, AuthSession
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
