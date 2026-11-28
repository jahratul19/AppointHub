from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, String, Text, Time, func
)
from .database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    photo_url = Column(String(1000), nullable=True)
    specialty = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    provider_name = Column(String(100), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True, index=True)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    status = Column(String(30), default="Pending", nullable=False)
    reason = Column(Text, nullable=True)
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

class AdminModerationLog(Base):
    __tablename__ = "admin_moderation_logs"

    id = Column(Integer, primary_key=True, index=True)

    admin_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    target_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    action = Column(String(20), nullable=False)

    reason = Column(String(500), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )


class UserActivity(Base):
    __tablename__ = "user_activity"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    account_identifier = Column(String(254), nullable=True, index=True)
    ip_address = Column(String(64), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(Text, nullable=False, default="")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )


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

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    can_view = Column(Boolean, default=True, nullable=False)
    can_create = Column(Boolean, default=False, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)
    can_manage_members = Column(Boolean, default=False, nullable=False)


class GroupResource(Base):
    __tablename__ = "group_resources"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(String(1000), nullable=False, default="")

