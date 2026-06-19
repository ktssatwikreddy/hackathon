from datetime import date, datetime

from pydantic import BaseModel, EmailStr

from app.models.core import UserRole
from app.schemas.base import ORMModel


class UserOut(ORMModel):
    id: int
    employee_code: str
    name: str
    email: EmailStr
    role: UserRole
    department_id: int | None
    phone: str | None
    designation: str | None
    joining_date: date | None
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    employee_code: str
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.employee
    department_id: int | None = None
    phone: str | None = None
    designation: str | None = None
    joining_date: date | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: UserRole | None = None
    department_id: int | None = None
    phone: str | None = None
    designation: str | None = None
    joining_date: date | None = None
    is_active: bool | None = None
