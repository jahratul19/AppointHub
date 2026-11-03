from fastapi import FastAPI

from app.database import Base, engine
from app.routes import router as appointment_router
from app import models

app = FastAPI(title="AppointHUB API")

# Create database tables
Base.metadata.create_all(bind=engine)

# Register Appointment CRUD routes
app.include_router(appointment_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def hello(name: str = "World") -> dict[str, str]:
    return {"message": f"Hello, {name}!"}