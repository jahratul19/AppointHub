from datetime import date, time
from pydantic import BaseModel, ConfigDict,EmailStr


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


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"