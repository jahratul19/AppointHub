
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import Appointment, User
from .schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    UserCreate,
    UserLogin,
)
from .security import (
    hash_password,
    verify_password,
    create_access_token,
)


# APPOINTMENT SERVICES

def create_appointment_service(
    appointment: AppointmentCreate,
    db: Session,
):
    db_appointment = Appointment(**appointment.model_dump())

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    return db_appointment


def get_appointments_service(db: Session):
    return db.query(Appointment).all()


def get_appointment_service(
    appointment_id: int,
    db: Session,
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    return appointment


def update_appointment_service(
    appointment_id: int,
    updated_data: AppointmentUpdate,
    db: Session,
):
    appointment = get_appointment_service(appointment_id, db)

    for key, value in updated_data.model_dump().items():
        setattr(appointment, key, value)

    db.commit()
    db.refresh(appointment)

    return appointment


def delete_appointment_service(
    appointment_id: int,
    db: Session,
):
    appointment = get_appointment_service(appointment_id, db)

    db.delete(appointment)
    db.commit()

    return {"message": "Appointment deleted successfully"}


# AUTHENTICATION SERVICES

def register_user_service(
    user_data: UserCreate,
    db: Session,
):
    existing_user = db.query(User).filter(
        (User.username == user_data.username)
        | (User.email == user_data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user_service(
    user_data: UserLogin,
    db: Session,
):
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not user or not verify_password(
        user_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
