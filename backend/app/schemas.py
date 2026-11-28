from datetime import date, time, datetime
from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator



class AppointmentCreate(BaseModel):
    doctor_id: int = Field(gt=0)
    appointment_date: date
    appointment_time: time
    reason: str = Field(min_length=3, max_length=2000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Reason must contain at least 3 non-space characters")
        return value


class AppointmentUpdate(BaseModel):
    doctor_id: int = Field(gt=0)
    appointment_date: date
    appointment_time: time
    reason: str = Field(min_length=3, max_length=2000)
    status: Literal["Pending", "Confirmed", "Completed", "Cancelled"]

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Reason must contain at least 3 non-space characters")
        return value


class AppointmentResponse(BaseModel):
    id: int
    customer_name: str
    provider_name: str
    doctor_id: int | None
    appointment_date: date
    appointment_time: time
    status: str
    reason: str | None

    model_config = ConfigDict(from_attributes=True)


class DoctorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    photo_url: str | None = Field(default=None, max_length=1000)
    specialty: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=4000)
    is_active: bool = True

    @field_validator("name", "specialty")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @field_validator("photo_url")
    @classmethod
    def validate_photo_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Photo URL must be an absolute HTTP or HTTPS URL")
        return value


class DoctorUpdate(DoctorCreate):
    pass


class DoctorResponse(BaseModel):
    id: int
    name: str
    photo_url: str | None
    specialty: str
    description: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_password(self):
        password = self.password
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain a lowercase letter")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain an uppercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain a number")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_new_password(self):
        password = self.new_password
        if not any(char.islower() for char in password):
            raise ValueError("New password must contain a lowercase letter")
        if not any(char.isupper() for char in password):
            raise ValueError("New password must contain an uppercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("New password must contain a number")
        return self


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AuthSessionResponse(BaseModel):
    id: int
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class AdminUserAction(BaseModel):
    reason: str

class AdminRoleUpdate(BaseModel):
    role: str

class AdminBulkUserAction(BaseModel):
    user_ids: list[int] = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)
    action: str


class AdminBulkDelete(BaseModel):
    record_ids: list[int] = Field(min_length=1, max_length=100)


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class GroupUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class GroupMemberCreate(BaseModel):
    email: EmailStr


class GroupPermissionUpdate(BaseModel):
    can_view: bool
    can_create: bool
    can_edit: bool
    can_delete: bool
    can_manage_members: bool

class GroupResourceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=1000)


class GroupResourceUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=1000)