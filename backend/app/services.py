
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, update
from datetime import datetime, timedelta, timezone

from .models import Appointment, Doctor, User, AuthSession
from .activity import recent_failed_logins, record_activity, request_ip

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

    expires_at = old_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
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

    revoked = db.execute(
        update(AuthSession)
        .where(
            AuthSession.id == old_session.id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
        .values(revoked_at=now)
        .execution_options(synchronize_session=False)
    )
    if revoked.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has already been used",
        )

    new_refresh_token = create_refresh_token()
    new_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(new_refresh_token),
        created_at=now,
        expires_at=now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_session)
    db.flush()
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "sid": str(new_session.id),
        }
    )
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
    }


def logout_user_session(refresh_token: str, db: Session) -> int | None:
    token_hash = hash_refresh_token(refresh_token)

    session = db.query(AuthSession).filter(
        AuthSession.refresh_token_hash == token_hash
    ).first()

    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.commit()
        return session.user_id
    return session.user_id if session else None


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
    doctor = db.query(Doctor).filter(
        Doctor.id == appointment.doctor_id,
        Doctor.is_active.is_(True),
    ).first()
    if doctor is None:
        existing_doctor = db.query(Doctor.id).filter(
            Doctor.id == appointment.doctor_id
        ).first()
        if existing_doctor:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This doctor is not accepting new appointments",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    db_appointment = Appointment(
        customer_name=current_user.username,
        provider_name=doctor.name,
        doctor_id=doctor.id,
        appointment_date=appointment.appointment_date,
        appointment_time=appointment.appointment_time,
        reason=appointment.reason.strip(),
        status="Pending",
        user_id=current_user.id,
    )

    db.add(db_appointment)
    db.flush()
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

    doctor = db.query(Doctor).filter(
        Doctor.id == updated_data.doctor_id,
        Doctor.is_active.is_(True),
    ).first()
    if doctor is None:
        existing_doctor = db.query(Doctor.id).filter(
            Doctor.id == updated_data.doctor_id
        ).first()
        if existing_doctor:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This doctor is not accepting new appointments",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    appointment.doctor_id = doctor.id
    appointment.provider_name = doctor.name
    appointment.appointment_date = updated_data.appointment_date
    appointment.appointment_time = updated_data.appointment_time
    appointment.reason = updated_data.reason.strip()
    appointment.status = updated_data.status

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
        username=user_data.username.strip(),
        email=str(user_data.email).strip().lower(),
        hashed_password=hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def login_user_service(
    user_data: UserLogin,
    db: Session,
    request,
):
    email = str(user_data.email).strip().lower()
    ip_address = request_ip(request)
    if recent_failed_logins(db, email, ip_address) >= 5:
        record_activity(
            db,
            "failed_login",
            request,
            account_identifier=email,
            details="Login temporarily rate-limited",
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again in 15 minutes.",
        )

    user = db.query(User).filter(
        func.lower(User.email) == email
    ).first()

    if not user or not verify_password(
        user_data.password,
        user.hashed_password,
    ):
        record_activity(
            db,
            "failed_login",
            request,
            account_identifier=email,
            details="Invalid credentials",
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_banned:
        record_activity(
            db,
            "failed_login",
            request,
            target_user_id=user.id,
            account_identifier=email,
            details="Banned account attempted login",
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been banned",
        )

    refresh_token, new_session = create_user_session(
        user_id=user.id,
        db=db,
    )
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "sid": str(new_session.id),
        }
    )
    record_activity(
        db,
        "login",
        request,
        actor_user_id=user.id,
        target_user_id=user.id,
        account_identifier=email,
    )
    db.commit()

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

    current_user.username = user_data.username.strip()
    current_user.email = str(user_data.email).strip().lower()

    db.commit()
    db.refresh(current_user)

    return current_user


def change_password_service(
    current_user: User,
    password_data: PasswordChange,
    db: Session,
    request,
):
    if not verify_password(
        password_data.current_password,
        current_user.hashed_password,
    ):
        record_activity(
            db,
            "failed_password_change",
            request,
            actor_user_id=current_user.id,
            target_user_id=current_user.id,
            account_identifier=current_user.email.lower(),
            details="Current password did not match",
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(
        password_data.new_password
    )

    # Revoke all active sessions
    active_sessions = db.query(AuthSession).filter(
        AuthSession.user_id == current_user.id,
        AuthSession.revoked_at.is_(None),
    ).all()

    for session in active_sessions:
        session.revoked_at = datetime.now(timezone.utc)

    record_activity(
        db,
        "password_change",
        request,
        actor_user_id=current_user.id,
        target_user_id=current_user.id,
    )
    db.commit()

    return {"message": "Password changed successfully"}