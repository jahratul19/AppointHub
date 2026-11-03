from datetime import date, time
from pydantic import BaseModel, ConfigDict


class AppointmentCreate(BaseModel):
    customer_name: str
    provider_name: str
    appointment_date: date
    appointment_time: time
    status: str = "Pending"


class AppointmentUpdate(BaseModel):
    customer_name: str
    provider_name: str
    appointment_date: date
    appointment_time: time
    status: str


class AppointmentResponse(AppointmentCreate):
    id: int

    model_config = ConfigDict(from_attributes=True) 