from conftest import client
from conftest import client, TestingSessionLocal
from app.security import create_access_token

def test_login_with_invalid_credentials():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code in [400, 401, 404]


def test_protected_route_without_token():
    response = client.get("/api/admin/dashboard/stats")

    assert response.status_code == 401

def test_normal_user_cannot_access_admin_stats():
    from app.models import User
    from app.security import hash_password

    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=hash_password("TestPassword123"),
        role="user",
        is_banned=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": "user"})
    db.close()

    response = client.get(
        "/api/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

def test_admin_can_access_admin_stats():
    from app.models import User
    from app.security import hash_password

    db = TestingSessionLocal()
    admin = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=hash_password("TestPassword123"),
        role="admin",
        is_banned=False,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    token = create_access_token({"sub": str(admin.id), "role": "admin"})
    db.close()

    response = client.get(
        "/api/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

def test_banned_user_cannot_access_admin_stats():
    from app.models import User
    from app.security import hash_password

    db = TestingSessionLocal()
    user = User(
        username="banneduser",
        email="banneduser@example.com",
        hashed_password=hash_password("TestPassword123"),
        role="admin",
        is_banned=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": "admin"})
    db.close()

    response = client.get(
        "/api/admin/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
