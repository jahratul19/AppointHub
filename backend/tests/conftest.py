
import os

# Use a temporary SQLite database for tests.
os.environ["DATABASE_URL"] = "sqlite:///./test_appoint_hub.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from main import app


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def pytest_configure():
    Base.metadata.create_all(bind=test_engine)


def pytest_unconfigure():
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)
