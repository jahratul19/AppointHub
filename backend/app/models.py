from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, String, Time
)
from .database import Base



class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    provider_name = Column(String(100), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    status = Column(String(30), default="Pending", nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # User permission role: user or admin
    role = Column(String(20), nullable=False, default="user", server_default="user")

    # Admin can ban or unban a user
    is_banned = Column(Boolean, nullable=False, default=False, server_default="false")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    refresh_token_hash = Column(String(255), nullable=False, unique=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

