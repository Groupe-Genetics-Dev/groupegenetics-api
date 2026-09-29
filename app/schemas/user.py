
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.incident import IncidentOut


class UserBase(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: UUID
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class UserMe(UserOut):
    role: str


class UserWithIncidents(UserOut):
    incidents: List[IncidentOut] = []


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str 
    new_password: str 
    confirm_password: str 


