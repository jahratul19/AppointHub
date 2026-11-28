import os
from datetime import date, datetime, time, timedelta, timezone

from app.database import Base, SessionLocal, engine
from app.models import (
    Appointment,
    Doctor,
    Group,
    GroupMember,
    GroupResource,
    User,
    UserActivity,
)
from app.security import hash_password
from app.migrations import migrate_appointment_doctor_fields


ACCOUNT_SPECS = [
    ("DEMO_ADMIN1", "admin", True, True, True),
    ("DEMO_ADMIN2", "admin", True, True, False),
    ("DEMO_USER1", "user", True, False, False),
    ("DEMO_USER2", "user", True, True, False),
    ("DEMO_USER3", "user", True, False, True),
]

DOCTOR_SPECS = [
    ("Dr. Ayesha Rahman", "Cardiology", None),
    ("Dr. Farhan Ahmed", "Dermatology", None),
    ("Dr. Nusrat Jahan", "Pediatrics", None),
]


def _account_values(prefix: str, role: str):
    username = os.environ[f"{prefix}_USERNAME"].strip()
    email = os.environ[f"{prefix}_EMAIL"].strip().lower()
    password = os.environ[f"{prefix}_PASSWORD"]
    if len(password) < 8 or not any(c.islower() for c in password) \
            or not any(c.isupper() for c in password) \
            or not any(c.isdigit() for c in password):
        raise ValueError(f"{prefix}_PASSWORD must meet the project password policy")
    return username, email, password, role


def main():
    Base.metadata.create_all(bind=engine)
    migrate_appointment_doctor_fields(engine)
    db = SessionLocal()
    try:
        doctors = []
        for name, specialty, photo_url in DOCTOR_SPECS:
            doctor = db.query(Doctor).filter(Doctor.name == name).first()
            if doctor is None:
                doctor = Doctor(
                    name=name,
                    specialty=specialty,
                    photo_url=photo_url,
                    description=f"Experienced {specialty.lower()} specialist available for appointments.",
                    is_active=True,
                )
                db.add(doctor)
                db.flush()
            else:
                doctor.specialty = specialty
                doctor.photo_url = photo_url
                doctor.description = (
                    f"Experienced {specialty.lower()} specialist available for appointments."
                )
                doctor.is_active = True
            doctors.append(doctor)

        accounts = []
        for index, (prefix, role, can_view, can_create, can_edit) in enumerate(ACCOUNT_SPECS, 1):
            username, email, password, account_role = _account_values(prefix, role)
            user = db.query(User).filter(User.email == email).first()
            is_new_user = user is None
            name_conflict = db.query(User).filter(
                User.username == username,
                User.email != email,
            ).first()
            if name_conflict:
                raise ValueError(f"Username {username!r} belongs to another account")
            if user is None:
                user = User(
                    username=username,
                    email=email,
                    hashed_password=hash_password(password),
                    role=account_role,
                    is_banned=False,
                )
                db.add(user)
                db.flush()
            else:
                user.username = username
                user.hashed_password = hash_password(password)
                user.role = account_role
                user.is_banned = False
            accounts.append((user, can_view, can_create, can_edit))
            if is_new_user:
                db.add(UserActivity(
                    actor_user_id=user.id,
                    target_user_id=user.id,
                    event_type="signup",
                    account_identifier=email,
                    details="Demo account provisioned",
                    created_at=datetime.now(timezone.utc),
                ))
            if db.query(Appointment).filter(Appointment.user_id == user.id).count() == 0:
                db.add(Appointment(
                    customer_name=username,
                    provider_name=doctors[(index - 1) % len(doctors)].name,
                    doctor_id=doctors[(index - 1) % len(doctors)].id,
                    appointment_date=date.today() + timedelta(days=index),
                    appointment_time=time(9 + index, 0),
                    status="Pending",
                    reason="Demo appointment booking",
                    user_id=user.id,
                ))
                db.add(UserActivity(
                    actor_user_id=user.id,
                    target_user_id=user.id,
                    event_type="record_created",
                    details="Demo appointment provisioned",
                    created_at=datetime.now(timezone.utc),
                ))

        owner = accounts[0][0]
        group_name = "AppointHUB Demo Team"
        group = db.query(Group).filter(
            Group.owner_id == owner.id,
            Group.name == group_name,
        ).first()
        if group is None:
            group = Group(name=group_name, owner_id=owner.id)
            db.add(group)
            db.flush()
            db.add(UserActivity(
                actor_user_id=owner.id,
                target_user_id=owner.id,
                event_type="group_created",
                details=group_name,
                created_at=datetime.now(timezone.utc),
            ))

        for user, can_view, can_create, can_edit in accounts:
            membership = db.query(GroupMember).filter(
                GroupMember.group_id == group.id,
                GroupMember.user_id == user.id,
            ).first()
            if membership is None:
                membership = GroupMember(group_id=group.id, user_id=user.id)
                db.add(membership)
            membership.can_view = can_view
            membership.can_create = can_create
            membership.can_edit = can_edit
            membership.can_delete = user.id == owner.id
            membership.can_manage_members = user.id == owner.id

        if db.query(GroupResource).filter(GroupResource.group_id == group.id).count() == 0:
            db.add(GroupResource(
                group_id=group.id,
                created_by=owner.id,
                title="Demo shared resource",
                description="Shared content for demonstrating team permissions.",
            ))
        db.commit()
        for user, *_ in accounts:
            print(f"user_id={user.id} username={user.username} role={user.role}")
        print(f"group_id={group.id} name={group.name} owner_user_id={owner.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
