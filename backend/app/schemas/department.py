from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import ORMModel


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class DepartmentOut(ORMModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
