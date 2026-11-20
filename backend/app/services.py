
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from .models import Appointment, User, AuthSession

from .schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    UserCreate,
    UserLogin,
    UserUpdate,
    PasswordChange,
)

from .security import (
    hash_password,
    verify_password,
    create_access_token,
    hash_refresh_token,
    create_refresh_token,
)


# SESSION SERVICES

REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_user_session(user_id: int, db: Session):
    refresh_token = create_refresh_token()
    now = datetime.now(timezone.utc)

    new_session = AuthSession(
        user_id=user_id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        created_at=now,
        expires_at=now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return refresh_token, new_session


def refresh_user_session(refresh_token: str, db: Session):
    token_hash = hash_refresh_token(refresh_token)

    old_session = db.query(AuthSession).filter(
        AuthSession.refresh_token_hash == token_hash
    ).first()

    if not old_session or old_session.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    now = datetime.now(timezone.utc)

    if old_session.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    user = db.query(User).filter(
        User.id == old_session.user_id
    ).first()

    if not user or user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable",
        )

    old_session.revoked_at = now

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )

    new_refresh_token, new_session = create_user_session(
        user_id=user.id,
        db=db,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
    }


def logout_user_session(refresh_token: str, db: Session):
    token_hash = hash_refresh_token(refresh_token)

    session = db.query(AuthSession).filter(
        AuthSession.refresh_token_hash == token_hash
    ).first()

    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()


def get_user_sessions(user_id: int, db: Session):
    return db.query(AuthSession).filter(
        AuthSession.user_id == user_id
    ).order_by(
        AuthSession.created_at.desc()
    ).all()


def revoke_user_session(
    session_id: int,
    user_id: int,
    db: Session,
):
    session = db.query(AuthSession).filter(
        AuthSession.id == session_id,
        AuthSession.user_id == user_id,
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()

    return {"message": "Session revoked successfully"}


# APPOINTMENT SERVICES


def create_appointment_service(
    appointment: AppointmentCreate,
    db: Session,
    current_user: User,
):
    db_appointment = Appointment(
        **appointment.model_dump(),
        user_id=current_user.id,
    )

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    return db_appointment


def get_appointments_service(
    db: Session,
    current_user: User,
):
    query = db.query(Appointment)

    if current_user.role != "admin":
        query = query.filter(
            Appointment.user_id == current_user.id
        )

    return query.all()


def get_appointment_service(
    appointment_id: int,
    db: Session,
    current_user: User,
):
    query = db.query(Appointment).filter(
        Appointment.id == appointment_id
    )

    if current_user.role != "admin":
        query = query.filter(
            Appointment.user_id == current_user.id
        )

    appointment = query.first()

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
    current_user: User,
):
    appointment = get_appointment_service(
        appointment_id, db, current_user
    )

    for key, value in updated_data.model_dump().items():
        setattr(appointment, key, value)

    db.commit()
    db.refresh(appointment)

    return appointment


def delete_appointment_service(
    appointment_id: int,
    db: Session,
    current_user: User,
):
    appointment = get_appointment_service(
        appointment_id, db, current_user
    )

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

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been banned",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )

    refresh_token, new_session = create_user_session(
        user_id=user.id,
        db=db,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }

def update_user_profile_service(
    current_user: User,
    user_data: UserUpdate,
    db: Session,
):
    existing_user = db.query(User).filter(
        User.id != current_user.id,
        (User.username == user_data.username)
        | (User.email == user_data.email),
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already in use",
        )

    current_user.username = user_data.username
    current_user.email = user_data.email

    db.commit()
    db.refresh(current_user)

    return current_user


def change_password_service(
    current_user: User,
    password_data: PasswordChange,
    db: Session,
):
    if not verify_password(
        password_data.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(
        password_data.new_password
    )

    db.commit()

    return {"message": "Password changed successfully"}
