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

from .database import get_db
from .models import User
from .schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    AuthSessionResponse,
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
)

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


# CREATE APPOINTMENT - PROTECTED
@router.post(
    "/appointments/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
        return create_appointment_service(appointment, db)


# READ ALL APPOINTMENTS
@router.get(
    "/appointments/",
    response_model=list[AppointmentResponse],
)
def get_appointments(db: Session = Depends(get_db)):
        return get_appointments_service(db)


# READ SINGLE APPOINTMENT
@router.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):

    return get_appointment_service(appointment_id, db)
    return appointment

# UPDATE APPOINTMENT
@router.put(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
)
def update_appointment(
    appointment_id: int,
    updated_data: AppointmentUpdate,
    db: Session = Depends(get_db),
):
    return update_appointment_service(appointment_id, updated_data, db)

    return appointment


# DELETE APPOINTMENT
@router.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    return delete_appointment_service(appointment_id, db)

    return {"message": "Appointment deleted successfully"}


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
