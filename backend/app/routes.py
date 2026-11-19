
from .services import (
    create_appointment_service,
    get_appointments_service,
    get_appointment_service,
    update_appointment_service,
    delete_appointment_service,
    register_user_service,
    login_user_service,
)
from fastapi import APIRouter, Depends, HTTPException, Response, status
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
)
from .security import (
    decode_access_token,
)

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

    if user is None:
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

    return new_user

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
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/api/auth",
    )

    return result
