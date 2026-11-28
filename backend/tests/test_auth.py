from datetime import datetime, timedelta, timezone
from uuid import uuid4

from conftest import client, TestingSessionLocal
from app.security import create_access_token
from app.models import AuthSession, User


def create_user_token(role="user", is_banned=False):
    from datetime import datetime, timedelta, timezone
    from app.security import create_refresh_token, hash_password, hash_refresh_token

    db = TestingSessionLocal()
    suffix = uuid4().hex
    user = User(
        username=f"tester_{suffix[:12]}",
        email=f"{suffix}@example.com",
        hashed_password=hash_password("TestPassword123"),
        role=role,
        is_banned=is_banned,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(create_refresh_token()),
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    token = create_access_token({
        "sub": str(user.id),
        "role": role,
        "sid": str(session.id),
    })
    db.close()
    return user.id, token

def test_login_with_invalid_credentials():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code in [400, 401, 404]


def test_login_rate_limit_is_applied_per_ip():
    email = f"{uuid4().hex}@example.com"
    headers = {"X-Forwarded-For": "192.0.2.55"}
    for _ in range(5):
        response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "WrongPassword1"},
            headers=headers,
        )
        assert response.status_code == 401
    limited = client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPassword1"},
        headers=headers,
    )
    assert limited.status_code == 429


def test_protected_route_without_token():
    response = client.get("/api/admin/dashboard/stats")

    assert response.status_code == 401

def test_normal_user_cannot_access_admin_stats():
    _, token = create_user_token()

    response = client.get(
        "/api/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

def test_admin_can_access_admin_stats():
    _, token = create_user_token(role="admin")

    response = client.get(
        "/api/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

def test_banned_user_cannot_access_admin_stats():
    _, token = create_user_token(role="admin", is_banned=True)

    response = client.get(
        "/api/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_missing_invalid_and_revoked_session_tokens_are_rejected():
    assert client.get("/api/auth/sessions").status_code == 401
    assert client.get(
        "/api/auth/sessions",
        headers={"Authorization": "Bearer not-a-jwt"},
    ).status_code == 401

    user_id, token = create_user_token()
    db = TestingSessionLocal()
    db.query(AuthSession).filter(AuthSession.user_id == user_id).update(
        {"revoked_at": datetime.now(timezone.utc)}
    )
    db.commit()
    db.close()
    response = client.get(
        "/api/auth/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_expired_access_token_is_rejected():
    from app.security import create_access_token

    user_id, _ = create_user_token()
    db = TestingSessionLocal()
    session = db.query(AuthSession).filter(AuthSession.user_id == user_id).first()
    token = create_access_token(
        {"sub": str(user_id), "role": "user", "sid": str(session.id)},
        expires_delta=timedelta(seconds=-1),
    )
    db.close()
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_login_refresh_and_logout_revoke_sessions():
    from app.security import hash_password

    db = TestingSessionLocal()
    suffix = uuid4().hex
    user = User(
        username=f"login_{suffix[:12]}",
        email=f"{suffix}@example.com",
        hashed_password=hash_password("TestPassword123"),
        role="user",
    )
    db.add(user)
    db.commit()
    email = user.email
    db.close()

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "TestPassword123"},
    )
    assert login.status_code == 200
    assert "httponly" in login.headers["set-cookie"].lower()
    old_token = login.json()["access_token"]
    assert client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {old_token}"},
    ).status_code == 200

    refreshed = client.post("/api/auth/refresh")
    assert refreshed.status_code == 200
    new_token = refreshed.json()["access_token"]
    assert client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {old_token}"},
    ).status_code == 401
    assert client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {new_token}"},
    ).status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {new_token}"},
    ).status_code == 401


def test_user_cannot_read_another_users_appointment():
    from app.models import Appointment
    from datetime import date, time

    owner_id, _ = create_user_token()
    _, token = create_user_token()
    db = TestingSessionLocal()
    appointment = Appointment(
        customer_name="Owner",
        provider_name="Provider",
        appointment_date=date(2026, 12, 1),
        appointment_time=time(10, 0),
        status="Pending",
        user_id=owner_id,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    appointment_id = appointment.id
    db.close()
    response = client.get(
        f"/api/appointments/{appointment_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_non_owner_cannot_manage_group_members():
    from app.models import Group, GroupMember

    owner_id, _ = create_user_token()
    member_id, member_token = create_user_token()
    db = TestingSessionLocal()
    group = Group(name="Private team", owner_id=owner_id)
    db.add(group)
    db.commit()
    db.refresh(group)
    db.add_all([
        GroupMember(group_id=group.id, user_id=owner_id, can_manage_members=True),
        GroupMember(group_id=group.id, user_id=member_id, can_manage_members=True),
    ])
    db.commit()
    group_id = group.id
    db.close()
    response = client.get(
        f"/api/groups/{group_id}/members",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert response.status_code == 403


def test_non_owner_cannot_rename_or_delete_group():
    from app.models import Group, GroupMember

    owner_id, _ = create_user_token()
    member_id, member_token = create_user_token()
    db = TestingSessionLocal()
    group = Group(name="Owner only", owner_id=owner_id)
    db.add(group)
    db.commit()
    db.refresh(group)
    db.add_all([
        GroupMember(group_id=group.id, user_id=owner_id, can_manage_members=True),
        GroupMember(group_id=group.id, user_id=member_id, can_manage_members=False),
    ])
    db.commit()
    group_id = group.id
    db.close()
    headers = {"Authorization": f"Bearer {member_token}"}
    assert client.put(
        f"/api/groups/{group_id}",
        json={"name": "Changed"},
        headers=headers,
    ).status_code == 403
    assert client.delete(
        f"/api/groups/{group_id}",
        headers=headers,
    ).status_code == 403


def test_group_resource_delete_is_owner_only():
    from app.models import Group, GroupMember, GroupResource

    owner_id, _ = create_user_token()
    member_id, member_token = create_user_token()
    db = TestingSessionLocal()
    group = Group(name="Owner deletes resources", owner_id=owner_id)
    db.add(group)
    db.commit()
    db.refresh(group)
    db.add_all([
        GroupMember(group_id=group.id, user_id=owner_id, can_manage_members=True),
        GroupMember(group_id=group.id, user_id=member_id, can_delete=True),
    ])
    resource = GroupResource(
        group_id=group.id,
        created_by=owner_id,
        title="Protected",
        description="",
    )
    db.add(resource)
    db.commit()
    group_id, resource_id = group.id, resource.id
    db.close()
    response = client.delete(
        f"/api/groups/{group_id}/resources/{resource_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert response.status_code == 403


def test_admin_bulk_delete_groups_removes_group_content_and_audits():
    from app.models import Group, GroupResource, UserActivity

    owner_id, _ = create_user_token()
    _, admin_token = create_user_token(role="admin")
    db = TestingSessionLocal()
    groups = [
        Group(name="Moderation team one", owner_id=owner_id),
        Group(name="Moderation team two", owner_id=owner_id),
    ]
    db.add_all(groups)
    db.commit()
    for group in groups:
        db.refresh(group)
        db.add(GroupResource(
            group_id=group.id,
            created_by=owner_id,
            title=f"Resource for {group.name}",
            description="",
        ))
    db.commit()
    group_ids = [group.id for group in groups]
    db.close()

    response = client.post(
        "/api/admin/content/groups/bulk-delete",
        json={"record_ids": group_ids},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["deleted_count"] == 2
    db = TestingSessionLocal()
    assert db.query(Group).filter(Group.id.in_(group_ids)).count() == 0
    assert db.query(GroupResource).filter(
        GroupResource.group_id.in_(group_ids)
    ).count() == 0
    assert db.query(UserActivity).filter(
        UserActivity.event_type == "delete_group",
    ).count() == 2
    db.close()


def test_doctor_directory_booking_ownership_and_deactivation():
    _, admin_token = create_user_token(role="admin")
    _, user_token = create_user_token()
    _, other_user_token = create_user_token()

    created = client.post(
        "/api/admin/doctors",
        json={
            "name": "Dr. Mina Karim",
            "photo_url": "https://example.test/mina.jpg",
            "specialty": "Cardiology",
            "description": "Heart health specialist.",
            "is_active": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert created.status_code == 201
    doctor = created.json()
    assert client.get("/api/doctors").json()[0]["id"] == doctor["id"]
    assert client.get(
        "/api/admin/doctors",
        headers={"Authorization": f"Bearer {user_token}"},
    ).status_code == 403

    booking = client.post(
        "/api/appointments/",
        json={
            "doctor_id": doctor["id"],
            "appointment_date": "2026-12-10",
            "appointment_time": "10:30:00",
            "reason": "Recurring headaches",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert booking.status_code == 201
    appointment = booking.json()
    assert appointment["doctor_id"] == doctor["id"]
    assert appointment["provider_name"] == "Dr. Mina Karim"
    assert appointment["reason"] == "Recurring headaches"
    assert client.get(
        f"/api/appointments/{appointment['id']}",
        headers={"Authorization": f"Bearer {other_user_token}"},
    ).status_code == 404

    deactivated = client.post(
        f"/api/admin/doctors/{doctor['id']}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False
    assert client.get("/api/doctors").json() == []
    rejected_booking = client.post(
        "/api/appointments/",
        json={
            "doctor_id": doctor["id"],
            "appointment_date": "2026-12-11",
            "appointment_time": "11:00:00",
            "reason": "Follow-up consultation",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert rejected_booking.status_code == 409


def test_appointment_migration_preserves_existing_rows():
    from sqlalchemy import create_engine, text
    from app.migrations import migrate_appointment_doctor_fields

    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE doctors (id INTEGER PRIMARY KEY)"
        ))
        connection.execute(text(
            "CREATE TABLE appointments ("
            "id INTEGER PRIMARY KEY, customer_name VARCHAR(100) NOT NULL, "
            "provider_name VARCHAR(100) NOT NULL, appointment_date DATE NOT NULL, "
            "appointment_time TIME NOT NULL, status VARCHAR(30) NOT NULL, user_id INTEGER)"
        ))
        connection.execute(text(
            "INSERT INTO appointments VALUES "
            "(41, 'Existing patient', 'Existing provider', "
            "'2026-12-01', '10:00:00', 'Pending', 7)"
        ))

    migrate_appointment_doctor_fields(engine)
    with engine.connect() as connection:
        row = connection.execute(text(
            "SELECT id, customer_name, provider_name, doctor_id, reason "
            "FROM appointments WHERE id = 41"
        )).one()
    assert tuple(row) == (
        41, "Existing patient", "Existing provider", None, None
    )
    engine.dispose()


def test_admin_cannot_ban_another_admin():
    _, admin_token = create_user_token(role="admin")
    target_id, _ = create_user_token(role="admin")
    response = client.put(
        f"/api/admin/users/{target_id}/ban",
        json={"reason": "Not permitted"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


def test_admin_detail_security_and_filtered_exports():
    from app.models import UserActivity

    admin_id, admin_token = create_user_token(role="admin")
    target_id, _ = create_user_token()
    db = TestingSessionLocal()
    db.add(UserActivity(
        actor_user_id=admin_id,
        target_user_id=target_id,
        event_type="login",
        account_identifier="demo@example.com",
        ip_address="192.0.2.12",
        user_agent="test browser",
        details="",
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()
    db.close()
    headers = {"Authorization": f"Bearer {admin_token}"}

    detail = client.get(f"/api/admin/users/{target_id}", headers=headers)
    assert detail.status_code == 200
    assert {"appointments", "groups", "sessions", "recent_activity"} <= set(detail.json())

    logs = client.get(
        "/api/admin/audit-logs?event_type=login&search=demo@example.com",
        headers=headers,
    )
    assert logs.status_code == 200
    assert logs.json()["total"] >= 1

    export = client.get("/api/admin/export/activity.csv?event_type=login", headers=headers)
    assert export.status_code == 200
    assert "text/csv" in export.headers["content-type"]
    assert "demo@example.com" in export.text

    denied = client.get("/api/admin/export/users.csv")
    assert denied.status_code == 401
