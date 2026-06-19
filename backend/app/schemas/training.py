from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.training import EnrollmentStatus, TrainingStatus
from app.schemas.base import ORMModel


class TrainingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None
    trainer_id: int | None = None
    department_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    capacity: int | None = Field(default=None, ge=1)
    status: TrainingStatus = TrainingStatus.draft


class TrainingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None
    trainer_id: int | None = None
    department_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    capacity: int | None = Field(default=None, ge=1)
    status: TrainingStatus | None = None


class TrainingOut(ORMModel):
    id: int
    title: str
    description: str | None
    category: str | None
    trainer_id: int | None
    department_id: int | None
    start_date: date | None
    end_date: date | None
    capacity: int | None
    status: TrainingStatus
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class EnrolledUser(ORMModel):
    id: int
    name: str
    email: str
    employee_code: str


class EnrollmentOut(ORMModel):
    id: int
    user_id: int
    training_id: int
    enrolled_on: datetime
    status: EnrollmentStatus
    user: EnrolledUser | None = None


class BulkEnrollRequest(BaseModel):
    user_ids: list[int] = Field(min_length=1)
