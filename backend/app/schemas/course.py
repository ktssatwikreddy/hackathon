from datetime import date, time

from pydantic import BaseModel, Field

from app.models.training import SessionMode
from app.schemas.session import SessionOut
from app.schemas.training import TrainingOut


class CourseSessionItem(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    session_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    mode: SessionMode = SessionMode.offline
    meeting_link: str | None = None


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category: str | None = None
    department_id: int | None = None
    trainer_id: int
    total_sessions: int | None = Field(default=None, ge=1)
    sessions: list[CourseSessionItem] = Field(min_length=1)


class CourseOut(TrainingOut):
    sessions: list[SessionOut] = []
